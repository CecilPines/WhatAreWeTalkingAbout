import json
import os
from collections import defaultdict


def extract_user_features(user_data):
    """从单用户爬取数据中提取画像特征"""
    if not user_data or 'user_info' not in user_data:
        return None  # 处理无效数据

    user_info = user_data['user_info']
    weibo_list = user_data.get('weibo_list', [])  # 微博内容列表

    # 1. 基本信息
    basic_info = {
        '用户ID': user_info.get('id', '未知'),
        '昵称': user_info.get('screen_name', '未知'),
        '性别': user_info.get('gender', '未知'),
        '地区': user_info.get('location', '未知'),
        '简介': user_info.get('description', '无简介'),
        '生日': user_info.get('birthday', '未知')
    }

    # 2. 社交属性
    social_info = {
        '粉丝数': user_info.get('followers_count', 0),
        '关注数': user_info.get('follow_count', 0),
        '微博数': user_info.get('statuses_count', 0),
        '认证类型': user_info.get('verified_type', '未认证'),
        '认证信息': user_info.get('verified_reason', '无')
    }

    # 3. 内容偏好（简单示例：提取最近5条微博的关键词，需结合分词工具）
    # （实际应用中可使用jieba分词+词云分析）
    content_keywords = []
    for weibo in weibo_list[:5]:  # 取前5条微博
        text = weibo.get('mblog', {}).get('text', '')
        # 简化处理：提取非HTML标签的文本（实际需清洗HTML）
        clean_text = text.replace('<br />', ' ').strip()
        if clean_text:
            content_keywords.append(clean_text[:20])  # 取前20字作为示例

    # 4. 互动特征（计算最近5条微博的平均互动量）
    interactions = []
    for weibo in weibo_list[:5]:
        mblog = weibo.get('mblog', {})
        interactions.append({
            '点赞': mblog.get('attitudes_count', 0),
            '转发': mblog.get('reposts_count', 0),
            '评论': mblog.get('comments_count', 0)
        })
    avg_interaction = {
        '平均点赞': sum(i['点赞'] for i in interactions) / len(interactions) if interactions else 0,
        '平均转发': sum(i['转发'] for i in interactions) / len(interactions) if interactions else 0,
        '平均评论': sum(i['评论'] for i in interactions) / len(interactions) if interactions else 0
    }

    # 整合所有特征
    user_profile = {
        '基本信息': basic_info,
        '社交属性': social_info,
        '内容偏好（示例）': content_keywords,
        '互动特征': avg_interaction
    }
    return user_profile

def save_profiles_to_json(profiles, filename='user_profiles.json'):
    """将用户画像列表保存为JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    print(f"用户画像已保存至 {filename}")



