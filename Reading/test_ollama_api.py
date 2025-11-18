import requests
import base64
import json
from pathlib import Path

# --- 配置 ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2-vision" 
# 请替换为您的 output/frames/ 目录下的第一帧图片路径
IMAGE_PATH = Path(r"E:\Program\Python\Program\SinaTopic-Test\Reading\video_analyzer\output\frames\frame_0.jpg")

def encode_image(image_path: Path) -> str:
    """将图像文件编码为 Base64 字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_ollama_vision():
    """直接向 Ollama API 发送请求，模拟 video-analyzer 行为"""
    print(f"--- 正在测试模型: {MODEL_NAME} ---")
    
    if not IMAGE_PATH.exists():
        print(f"错误：图片文件未找到在 {IMAGE_PATH}")
        return

    try:
        base64_image = encode_image(IMAGE_PATH)
        print(f"图片已编码为 Base64. 正在发送请求到 {OLLAMA_URL}...")
        print("Done0")

        # 构建请求 JSON
        data = {
            "model": MODEL_NAME,
            "prompt": "Describe the main action in this soccer image in detail.",
            "stream": False,
            "images": [base64_image]  # 传递 Base64 编码的图像
        }
        print("Done1")
        # 发送请求
        response = requests.post(OLLAMA_URL, json=data)
        print("Done1.5")
        response.raise_for_status() # 如果状态码不是 2xx，则抛出 HTTPError
        print("Done2")

        # 解析响应
        json_response = response.json()
        print("Done3")

        if 'response' in json_response:
            print("\n✅ API 测试成功！模型返回了描述。")
            print("-" * 20)
            print(json_response['response'][:500] + "...")
        else:
            print("\n❌ API 测试失败，响应中缺少 'response' 字段。")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API 错误：HTTP Status {e.response.status_code}")
        if e.response.status_code == 500:
            print("🛑 错误原因：500 内部错误。模型可能因内存/显存不足而崩溃。")
        else:
            print(f"详细错误: {e}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接错误：无法连接到 Ollama 服务。请确认 Ollama 已启动。")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    test_ollama_vision()