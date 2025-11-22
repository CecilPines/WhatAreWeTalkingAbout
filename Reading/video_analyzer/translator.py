import logging
import requests
from typing import Dict, Any

# 配置日志记录
logger = logging.getLogger(__name__)

def translate_summary_to_chinese(
    data: dict, 
    model_name: str, 
    api_key: str, 
    api_url: str
) -> dict:
    """
    使用 OpenAI 兼容的 API 模型（如 DeepSeek, OpenRouter）翻译 JSON 数据中的 'summary' 字段为中文。

    Args:
        data: 包含英文摘要的字典（通常是 video_description）。
        model_name: 用于翻译的 API 模型名称 (e.g., "deepseek-ai/DeepSeek-V3", "gpt-3.5-turbo")。
        api_key: API 密钥。
        api_url: API 服务地址 (e.g., "https://api.siliconflow.cn/v1")。

    Returns:
        更新了 'chinese_summary' 字段的字典。
    """
    # 1. 获取待翻译文本
    english_summary = data.get('summary')
    
    if not english_summary or not isinstance(english_summary, str):
        logger.warning("JSON data does not contain a valid 'summary' string. Skipping API translation.")
        return data

    # 2. 记录日志 (注意：这里明确显示是 API 翻译)
    logger.info(f"Starting API translation using model: {model_name} via {api_url}...")
    
    # 3. 构造提示词 (System Prompt + User Prompt)
    system_prompt = (
        "You are an expert translator. Your task is to accurately and fluently translate "
        "the following video summary into Simplified Chinese. "
        "You MUST only output the translated text, do not add any explanation, "
        "markdown headers, or surrounding commentary."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": english_summary}
    ]
    
    # 4. 构造请求头和数据
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    json_data = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1, # 翻译任务使用低温度以保证准确性
        "max_tokens": 2000  # 预留足够的 Tokens 给中文输出
    }
    
    # 确保 URL 格式正确 (追加 /chat/completions)
    full_url = f"{api_url.rstrip('/')}/chat/completions"

    try:
        # 5. 发送 HTTP POST 请求
        response = requests.post(full_url, headers=headers, json=json_data, timeout=60)
        response.raise_for_status() # 检查 HTTP 错误 (如 401, 404, 500)
        
        # 6. 解析响应
        json_response = response.json()
        
        # 提取内容 (兼容 OpenAI 格式)
        if 'choices' in json_response and len(json_response['choices']) > 0:
            chinese_summary = json_response['choices'][0]['message']['content'].strip()
            
            # 7. 将结果存回字典
            data['chinese_summary'] = chinese_summary
            logger.info("API Translation successful.")
        else:
            error_msg = f"API response format unexpected: {json_response}"
            logger.error(error_msg)
            data['translation_error'] = error_msg
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Translation Network Error: {e}")
        data['translation_error'] = f"Translation Failed: Network Error ({e})"
    except Exception as e:
        logger.error(f"An unexpected error occurred during API translation: {e}")
        data['translation_error'] = f"Translation Failed: Logic Error ({e})"

    return data