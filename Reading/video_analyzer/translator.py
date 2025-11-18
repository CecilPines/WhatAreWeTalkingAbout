import ollama
import logging
import json # 尽管我们主要处理字典，但导入 json 以防需要序列化/反序列化

# 配置日志记录，以便在运行中看到翻译状态
logger = logging.getLogger(__name__)

# --- 翻译函数 ---
def translate_summary_to_chinese(data: dict, model_name: str, ollama_host: str = "http://localhost:11434") -> dict:
    """
    使用本地 Ollama 模型翻译 JSON 数据中的 'summary' 字段为中文。

    Args:
        data: 包含英文摘要的字典（analysis.json 的内容）。
        model_name: 用于翻译的 Ollama 模型名称（e.g., "llama3.2-vision"）。
        ollama_host: Ollama 服务的地址。

    Returns:
        更新了 'chinese_summary' 字段的字典。
    """
    english_summary = data.get('summary')
    
    if not english_summary or not isinstance(english_summary, str):
        logger.warning("JSON data does not contain a valid 'summary' string. Skipping translation.")
        return data

    logger.info(f"Starting translation using Ollama model: {model_name}...")
    TARGET_LANGUAGE = "Simplified Chinese"

    try:
        # 1. 初始化 Ollama 客户端
        client = ollama.Client(host=ollama_host)
        
        # 2. 构建翻译提示词
        system_prompt = (
            f"You are an expert translator. Your task is to accurately and fluently translate "
            f"the following video summary into {TARGET_LANGUAGE}. "
            f"You MUST only output the translated text, do not add any "
            f"explanation, markdown headers, or surrounding commentary."
        )
        
        user_prompt = f"Video Summary to translate:\n---\n{english_summary}"

        # 3. 调用 Ollama API
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=False 
        )
        
        chinese_summary = response['message']['content'].strip()
        
        # 4. 将中文翻译结果添加到数据字典中
        data['chinese_summary'] = chinese_summary
        logger.info("Translation successful. Chinese summary added to output.")
        
    except ollama.ResponseError as e:
        logger.error(f"Ollama Error: Failed to translate. Check if service is running and model '{model_name}' exists. Error: {e}")
        data['translation_error'] = f"Translation Failed: Ollama Error ({e})"
    except Exception as e:
        logger.error(f"An unexpected error occurred during translation: {e}")
        data['translation_error'] = f"Translation Failed: Unknown Error ({e})"

    return data