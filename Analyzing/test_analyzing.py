import os
import sys
import threading
import time
import pandas
from dotenv import load_dotenv, set_key, dotenv_values

from GetOutput import get_output_dir, get_project_root
from Spidering.backend import WeiboDeepAnalyzer
from Reading.video_analyzer.cli import video_main
from Picturing.weibo_user_picture import get_weibo_users_pic
from Analyzing.step1_cut_words.test_cut_words import get_comments, get_data, extract_key
from Analyzing.step2_word_cloud.test_word_cloud import get_word_cloud
from Analyzing.step3_extration_classification.backend.demo import get_predict
from WebUI.test_paddle import process_ocr

# 加载 .env 文件
dotenv_path = os.path.join(get_project_root(), 'Spidering', '.env')
def get_wid_from_env():
    """从 .env 文件中读取 WID 的值"""
    load_dotenv(dotenv_path, override=True)
    config = dotenv_values(dotenv_path)  # 获取所有配置的键值对
    wid = config.get('WID')  # 获取 WID 的值
    return wid

def Reading():
    """读取阶段"""
    result_data["reading_texts"] = []
    try:
        print(f"开始处理 {len(result_data['page_images'])} 张图片...")
        for image in result_data["page_images"]:
            image_path = os.path.join(get_output_dir(), image)
            print(f"处理图片: {image_path}")
            try:
                ocr_result = process_ocr(image_path)
                result_data["reading_texts"].append(ocr_result)
                print(f"图片 {image} 处理完成")
            except Exception as e:
                print(f"处理图片 {image} 时出错: {e}")
                import traceback
                traceback.print_exc()
        print(f"Reading阶段完成，共处理 {len(result_data['reading_texts'])} 个结果")
    except Exception as e:
        print(f"Reading阶段发生错误: {e}")
        import traceback
        traceback.print_exc()

def Analyzing():
    """分析阶段"""
    # time.sleep(2)
    wid = get_wid_from_env()
    """微博内容分析"""
    print("1/5 - 1/3 微博内容合并开始...")
    print("1/5 - 1/3 微博内容合并开始...")
    with open(os.path.join(get_output_dir(), "weibo.txt"), "w", encoding="utf-8") as f:
        for text in result_data["page_text_1"]:
            # Ensure text is a string (join if it's a list)
            if isinstance(text, list):
                text = " ".join(text)  # Or join using other separator if needed
            print(f"done1 - {text}")
            f.write(text + '\n')
        print("done1")

        for text in result_data["reading_texts"]:
            # Ensure text is a string (join if it's a list)
            if isinstance(text, list):
                text = " ".join(text)  # Or join using other separator if needed
            print(f"done2 - {text}")
            f.write(text + '\n')
        print("done2")

    print("1/5 - 2/3 词转换开始...")
    get_data(os.path.join(get_output_dir(), "weibo.txt"), os.path.join(get_output_dir(), "weibo_cut.dat"))
    print("1/5 - 3/3 关键词提取开始...")
    extract_key(os.path.join(get_output_dir(), "weibo_cut.dat"),
                os.path.join(get_output_dir(), "weibo_keyword.dat"))
    print("2/5 正在绘制词云图...")
    get_word_cloud(os.path.join(get_output_dir(), "weibo_keyword.dat"), "weibo")


    """评论分析"""
    csv_path = os.path.join(get_project_root(), "Spidering", "backend", "weibo_analysis", wid, wid+"_comments.csv")
    print("3/5 - 1/3 评论合并开始...")
    get_comments(csv_path)
    print("3/5 - 2/3 词转换开始...")
    get_data(os.path.join(get_output_dir(),"comments.txt"), os.path.join(get_output_dir(),"comments_cut.dat"))
    print("3/5 - 3/3 关键词提取开始...")
    extract_key(os.path.join(get_output_dir(),"comments_cut.dat"), os.path.join(get_output_dir(),"comments_keyword.dat"))
    print("4/5 正在绘制词云图...")
    get_word_cloud(os.path.join(get_output_dir(), "comments_keyword.dat"), "comments")


    """整体进行情感倾向分析"""
    print("5/5 正在分析情感倾向...")
    target_path_list = [os.path.join(get_output_dir(), "weibo.txt"), os.path.join(get_output_dir(), "comments.txt")]
    name_list = ["weibo", "comments"]
    get_predict(target_path_list, name_list)

if __name__ == "__main__":
    global result_data
    wid = get_wid_from_env()
    result_data = {
        "page_text_1": [],
        "reading_texts": [],
        "page_images": [wid+"_1.jpg",wid+"_2.jpg",wid+"_3.jpg"]
    }
    Reading()
    Analyzing()