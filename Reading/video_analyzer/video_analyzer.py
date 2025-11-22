import os
import json
import dashscope
from dashscope import MultiModalConversation

# 【重要】请将此处替换为您的阿里云 DashScope API Key
# 建议设置在环境变量中: export DASHSCOPE_API_KEY='your_key'
dashscope.api_key = "sk-21d9e8dbe9f64951bb61ebf6d7d31d2f" 

def analyze_video_with_qwen_local(local_video_path_raw):
    """
    使用 qwen3-vl-flash 模型分析本地视频文件，输出结构化事件和总结。
    """
    print(f"--- 正在处理视频: {local_video_path_raw} ---")

    # 1. 构建本地文件 URL
    # Windows 路径需要转换为 URI 格式，例如: file://C:/Users/YSH/Desktop/test.mp4
    # 对于 Windows，建议将反斜杠 \ 替换为正斜杠 / 以避免转义问题
    formatted_path = local_video_path_raw.replace("\\", "/")
    
    # 确保路径以 file:// 开头
    if not formatted_path.startswith("file://"):
        # Windows 路径通常以盘符开头 (例如 C:/)，需要在前面加上 file://
        if ":" in formatted_path: 
             video_url = f"file://{formatted_path}"
        # Linux/macOS 路径通常以 / 开头，需要在前面加上 file://
        elif formatted_path.startswith("/"):
             video_url = f"file://{formatted_path}"
        else:
            # 如果是相对路径，先转换为绝对路径
            abs_path = os.path.abspath(formatted_path).replace("\\", "/")
            video_url = f"file://{abs_path}"
    else:
        video_url = formatted_path

    print(f"本地视频 URL: {video_url}")

    # 2. 构建提示词 (Prompt Engineering)
    system_prompt = "你是一个专业的视频分析助手。请仔细观看视频，并按要求输出分析结果。"
    user_prompt = """
请分析这段视频的内容，并完成以下两个任务：

任务一：提取视频中的关键事件。
请严格按照以下 JSON 格式输出事件列表，不要包含任何 Markdown 格式标记（如 ```json）：
[
    {
        "start_time": "HH:mm:ss",
        "end_time": "HH:mm:ss",
        "event": "事件的详细中文描述"
    }
]

任务二：总结视频内容。
在 JSON 数据输出结束后，另起一行，以“【视频总结】”开头，对视频发生的整体内容进行一段通顺的中文总结。

请确保时间戳格式严格为 HH:mm:ss。
"""

    # 3. 调用 qwen3-vl-flash 模型
    messages = [
        {
            "role": "system",
            "content": [{"text": system_prompt}]
        },
        {
            "role": "user",
            "content": [
                # 使用 file:// 格式的本地路径
                {"video": video_url}, 
                {"text": user_prompt}
            ]
        }
    ]

    print("正在调用 qwen3-vl-flash 模型进行分析...")
    try:
        response = MultiModalConversation.call(
            model='qwen3-vl-flash',
            messages=messages,
            stream=False
        )
    except Exception as e:
        print(f"模型调用失败: {e}")
        return

    # 4. 处理和展示输出结果
    if response.status_code == 200:
        try:
            content = response.output.choices[0].message.content[0]['text']
            
            print("\n" + "="*20 + " 模型原始输出 " + "="*20)
            print(content)
            print("="*50 + "\n")

            # 尝试提取和格式化 JSON
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx+1]
                events = json.loads(json_str)
                
                print("--- 提取的结构化事件 (JSON) ---")
                print(json.dumps(events, indent=4, ensure_ascii=False))

                return json.dumps(events, indent=4, ensure_ascii=False)
            
            # 提取总结部分
            summary_marker = "【视频总结】"
            summary_idx = content.find(summary_marker)
            if summary_idx != -1:
                print("\n--- 视频总结 ---")
                print(content[summary_idx + len(summary_marker):].strip())

            return content
                
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
             print(f"结果解析失败: {e}。请查看上方的模型原始输出。")
    else:
        print(f"请求失败: Code {response.code}, Message {response.message}")

# 使用示例
if __name__ == "__main__":
    # 【重要】请替换为您本地视频的绝对路径
    # 例如 Windows: r"C:\Users\YSH\Desktop\test.mp4"
    # 例如 Linux/macOS: "/home/user/videos/test.mp4"
    local_video_path_raw = r"C:\Users\YSH\Desktop\test.mp4"
    
    # 检查文件是否存在
    if os.path.exists(local_video_path_raw):
        analyze_video_with_qwen_local(local_video_path_raw)
    else:
        print(f"错误: 找不到文件 {local_video_path_raw}，请检查路径。")