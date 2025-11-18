import json
import os.path

from openai import OpenAI  # 以OpenAI为例，其他模型需替换
from GetOutput import get_output_dir


# 生成整体用户画像分析
def generate_overall_profile_analysis(user_profiles, api_key):
    client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

    # 构建整体分析的提示词
    prompt = f"""
    请基于以下所有微博用户的基础信息、社交行为和内容偏好，生成一份整体用户画像分析。
    分析结果必须严格以关键词及短语的形式呈现，每个分析维度用清晰的标题区分，具体要求如下：

    1. 群体核心标签（3-5个）：直接列出最具代表性的标签，用逗号分隔
    2. 整体兴趣偏好分布：以"话题类别:占比描述"的格式呈现，如"娱乐:高占比，科技:中等"
    3. 共同社交特征：列出3-5个核心社交行为特征，用短句或短语
    4. 群体潜在需求：提炼3-5个关键需求点，用名词或动宾短语
    5. 不同用户类型的分类及特征：以"类型名称:核心特征(关键词)"的格式呈现

    所有用户数据如下：
    {json.dumps(user_profiles, ensure_ascii=False, indent=2)}
    
    请注意：无需任何多余解释，仅返回结构化的关键词及短语结果，确保简洁明了、易于提取关键信息。
    """

    try:
        response = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[
                {"role": "system", "content": "你是一位社交媒体用户群体分析专家，擅长从多用户数据中提炼群体特征。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"大模型调用失败: {e}")
        return None


# 批量处理并保存整体分析结果
def batch_user_profile_analysis(api_key, user_profiles):
    if not user_profiles:
        print("没有有效的用户数据可分析")
        return

    print("正在生成整体用户画像分析...")
    analysis = generate_overall_profile_analysis(user_profiles, api_key)

    if analysis:
        # 保存整体分析结果
        analysis_output = os.path.join(get_output_dir(), "overall_user_analysis.txt")
        with open(analysis_output, 'w', encoding='utf-8') as f:
            f.write(analysis)
        print("整体用户画像分析已保存至 overall_user_analysis.txt")

        return analysis

    return ""


if __name__ == '__main__':
    pass