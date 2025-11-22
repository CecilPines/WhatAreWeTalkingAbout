import argparse
from pathlib import Path
import json
import logging
import shutil
import sys
from typing import Optional
import torch
import torch.backends.mps

# 使用相对导入，确保在模块模式下运行正常
from .config import Config, get_client, get_model
from .frame import VideoProcessor
from .prompt import PromptLoader
from .analyzer import VideoAnalyzer
from .audio_processor import AudioProcessor, AudioTranscript
from .clients.ollama import OllamaClient
from .clients.generic_openai_api import GenericOpenAIAPIClient
from .translator import translate_summary_to_chinese

# Initialize logger at module level
logger = logging.getLogger(__name__)

def get_log_level(level_str: str) -> int:
    """Convert string log level to logging constant."""
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)

def cleanup_files(output_dir: Path):
    """Clean up temporary files and directories."""
    try:
        frames_dir = output_dir / "frames"
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
            logger.debug(f"Cleaned up frames directory: {frames_dir}")
            
        audio_file = output_dir / "audio.wav"
        if audio_file.exists():
            audio_file.unlink()
            logger.debug(f"Cleaned up audio file: {audio_file}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def create_client(config: Config):
    """Create the appropriate client based on configuration."""
    client_type = config.get("clients", {}).get("default", "ollama")
    client_config = get_client(config)
    
    if client_type == "ollama":
        return OllamaClient(client_config["url"])
    elif client_type == "openai_api":
        return GenericOpenAIAPIClient(client_config["api_key"], client_config["api_url"])
    else:
        raise ValueError(f"Unknown client type: {client_type}")

def video_main(file_path):
    parser = argparse.ArgumentParser(description="Analyze video using Vision models")
    
    parser.add_argument("--config", type=str, default="config",
                        help="Path to configuration directory")
    parser.add_argument("--output", type=str, help="Output directory for analysis results")
    parser.add_argument("--client", type=str, help="Client to use (ollama or openrouter)")
    parser.add_argument("--ollama-url", type=str, help="URL for the Ollama service")
    parser.add_argument("--api-key", type=str, help="API key for OpenAI-compatible service")
    parser.add_argument("--api-url", type=str, help="API URL for OpenAI-compatible API")
    parser.add_argument("--model", type=str, help="Name of the vision model to use")
    parser.add_argument("--duration", type=float, help="Duration in seconds to process")
    parser.add_argument("--keep-frames", action="store_true", help="Keep extracted frames after analysis")
    parser.add_argument("--whisper-model", type=str, help="Whisper model size (tiny, base, small, medium, large), or path to local Whisper model snapshot")
    parser.add_argument("--start-stage", type=int, default=1, help="Stage to start processing from (1-3)")
    parser.add_argument("--max-frames", type=int, default=sys.maxsize, help="Maximum number of frames to process")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level (default: INFO)")
    parser.add_argument("--prompt", type=str, default="",
                        help="Question to ask about the video")
    parser.add_argument("--language", type=str, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--temperature", type=float, help="Temperature for LLM generation")
    
    # 解析参数 (允许为空列表，因为主要依赖 config 和 file_path)
    args = parser.parse_args()

    # Set up logging
    log_level = get_log_level(args.log_level)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    logger.setLevel(log_level)

    # Load configuration
    config = Config(args.config)
    config.update_from_args(args)

    # Validate file path
    if not file_path:
        raise ValueError("Video path must be provided via the main script execution logic.")
        
    video_path = Path(file_path)
    output_dir = Path(config.get("output_dir"))
    
    try:
        client = create_client(config)
        model = get_model(config)
        prompt_loader = PromptLoader(config.get("prompt_dir"), config.get("prompts", []))
        
        transcript = None
        frames = []
        frame_analyses = []
        video_description = None

        # Stage 1: Frame and Audio Processing
        if args.start_stage <= 1:
            logger.debug("Initializing audio processing...")
            audio_processor = AudioProcessor(
                language=config.get("audio", {}).get("language", ""), 
                model_size_or_path=config.get("audio", {}).get("whisper_model", "medium"),
                device=config.get("audio", {}).get("device", "cpu")
            )
            
            logger.info("Extracting audio from video...")
            try:
                audio_path = audio_processor.extract_audio(video_path, output_dir)
            except Exception as e:
                logger.error(f"Error extracting audio: {e}")
                audio_path = None
            
            if audio_path is None:
                logger.debug("No audio found in video - skipping transcription")
                transcript = None
            else:
                logger.info("Transcribing audio...")
                transcript = audio_processor.transcribe(audio_path)
                if transcript is None:
                    logger.warning("Could not generate reliable transcript. Proceeding with video analysis only.")
            
            logger.info(f"Extracting frames from video using model {model}...")
            processor = VideoProcessor(video_path, output_dir / "frames", model)
            frames = processor.extract_keyframes(
                frames_per_minute=config.get("frames", {}).get("per_minute", 60),
                duration=config.get("duration"),
                max_frames=args.max_frames
            )
            
        # Stage 2: Frame Analysis
        if args.start_stage <= 2:
            logger.info("Analyzing frames...")
            analyzer = VideoAnalyzer(
                client, 
                model, 
                prompt_loader,
                config.get("clients", {}).get("temperature", 0.2),
                config.get("prompt", "")
            )
            frame_analyses = []
            for frame in frames:
                analysis = analyzer.analyze_frame(frame)
                frame_analyses.append(analysis)
                
        # Stage 3: Video Reconstruction
        if args.start_stage <= 3:
            logger.info("Reconstructing video description...")
            video_description = analyzer.reconstruct_video(
                frame_analyses, frames, transcript
            )
        
        # --- [修正后的 API 翻译逻辑] ---
        if video_description and video_description.get("response"):
            logger.info("Translating video description to Chinese via API...")
            
            translation_model = get_model(config) 
            api_config = config.get("clients", {}).get("openai_api", {})
            api_key = api_config.get("api_key")
            api_url = api_config.get("api_url")
            
            if not api_key or not api_url:
                logger.warning("API key or URL not configured for translation. Skipping API translation.")
            else:
                data_to_translate = {'summary': video_description.get("response")}
                
                try:
                    # 修正：传递 api_key 和 api_url，而不是 ollama_host
                    translated_data = translate_summary_to_chinese(
                        data=data_to_translate,
                        model_name=translation_model,
                        api_key=api_key,
                        api_url=api_url
                    )
                    
                    if translated_data.get('chinese_summary'):
                        video_description['chinese_summary'] = translated_data['chinese_summary']
                        logger.info("Translation successful.")
                    elif translated_data.get('translation_error'):
                         logger.warning(f"Translation failed: {translated_data['translation_error']}")
                except Exception as e:
                    logger.error(f"Error calling translation module: {e}")
        # --- [翻译逻辑结束] ---

        output_dir.mkdir(parents=True, exist_ok=True)
        results = {
            "metadata": {
                "client": config.get("clients", {}).get("default"), 
                "model": model, 
                "whisper_model": config.get("audio", {}).get("whisper_model"),
                "frames_per_minute": config.get("frames", {}).get("per_minute"),
                "duration_processed": config.get("duration"),
                "frames_extracted": len(frames),
                "frames_processed": min(len(frames), args.max_frames),
                "start_stage": args.start_stage,
                "audio_language": transcript.language if transcript else None,
                "transcription_successful": transcript is not None
            },
            "transcript": {
                "text": transcript.text if transcript else None,
                "segments": transcript.segments if transcript else None
            } if transcript else None,
            "frame_analyses": frame_analyses,
            "video_description": video_description
        }
        
        with open(output_dir / "analysis.json", "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info("\nTranscript:")
        if transcript:
            logger.info(transcript.text)
        else:
            logger.info("No reliable transcript available")
            
        if video_description:
            logger.info("\nVideo Description:")
            logger.info(video_description.get("response", "No description generated"))
            if video_description.get('chinese_summary'):
                logger.info("\n中文翻译:")
                logger.info(video_description['chinese_summary'])
        
        if not config.get("keep_frames"):
            cleanup_files(output_dir)
        
        logger.info(f"Analysis complete. Results saved to {output_dir / 'analysis.json'}")
        return video_description['chinese_summary']
            
    except Exception as e:
        logger.error(f"Error during video analysis: {e}")
        if not config.get("keep_frames"):
            cleanup_files(output_dir)
        raise

if __name__ == "__main__":
    # 用户指定的文件路径
    file_path = r"C:\Users\YSH\Desktop\WhatAreWeTalkingAbout-master\Reading\test.mp4"
    video_main(file_path)