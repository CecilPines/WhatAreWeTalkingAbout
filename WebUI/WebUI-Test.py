from flask import Flask, render_template, request, jsonify, redirect, url_for
import os

# Flask 实例化时配置静态文件夹
app = Flask(__name__,template_folder=os.path.join(os.path.dirname(__file__), 'WebUI', 'templates'))

import threading
import time
import os
import pandas
from dotenv import load_dotenv, set_key, dotenv_values

from GetOutput import get_output_dir, get_project_root
from Spidering.backend import WeiboDeepAnalyzer
from test_download_video import get_video_url, download_video
from test_mid2wid import get_dict, mid_to_wid
from test_paddle import process_ocr
from Reading.video_analyzer.cli import video_main
from Picturing.weibo_user_picture import get_weibo_users_pic

# 加载 .env 文件
dotenv_path = os.path.join(get_project_root(), 'Spidering', '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)

progress = {"status": "idle", "step": 0, "message": ""}
result_data = {}
video_flag = False
image_flag = False
picture_users_list = []

def Spidering():
    """模拟爬取阶段"""
    global video_flag, image_flag
    progress["message"] = "正在爬取微博内容..."

    analyzer = WeiboDeepAnalyzer.WeiboDeepAnalyzer()  # 所有参数从.env文件读取
    analyzer.analyze()  # max_comment_pages和max_repost_pages从.env读取
    # 获取wid
    wid = get_wid_from_env()
    # time.sleep(2)

    result_data["screenshot"] = "screenshot.png"

    spidering_result_path = os.path.join(get_project_root(), "Spidering", "backend", "weibo_analysis", wid)
    df_weibo = pandas.read_csv(os.path.join(spidering_result_path, wid+"_weibo.csv"), encoding='utf-8')
    df_comments = pandas.read_csv(os.path.join(spidering_result_path, wid+"_comments.csv"), encoding='utf-8')
    df_repost = pandas.read_csv(os.path.join(spidering_result_path, wid+"_reposts.csv"), encoding='utf-8')

    result_data["page_text"] = []
    for index, row in df_weibo.iterrows():
        result_data["page_text"].append(row.tolist())
    for index, row in df_comments.iterrows():
        result_data["page_text"].append(row.tolist())

    global picture_users_list
    picture_users_list += df_comments['评论者ID'].tolist()
    picture_users_list += df_repost['转发者ID'].tolist()
    print(picture_users_list)

    # 若爬取出图片和视频
    """若有爬取到图片则添加图片"""

    result_data["page_images"] = []
    # 遍历目录中的文件
    for filename in os.listdir(get_output_dir()):
        # 仅考虑以 'wid_' 开头且以 '.jpg' 结尾的文件
        if filename.startswith(wid) and filename.endswith('.jpg'):
            result_data["page_images"].append(filename)
    if result_data["page_images"]:
        image_flag = True

    """若有爬取到视频链接则下载视频并添加"""
    result_data["page_videos"] = []
    page_url_list = df_weibo['视频链接'][0]
    # 获取视频的真实 URL
    index = 1
    try:
        for page_url in page_url_list:
            video_url = get_video_url(page_url)
            if video_url:
                # 设置保存路径
                output_path = os.path.join(get_output_dir(), "weibo_video.mp4")
                # 下载视频
                download_video(video_url, output_path)
            result_data["page_videos"].append("weibo_video_" + str(index) + ".mp4")
            index += 1
    except Exception:
        print("No Video")
        pass
    if result_data["page_videos"]:
        video_flag = True

    progress["step"] = 25


def Reading():
    """模拟读取阶段"""
    progress["message"] = "正在读取微博数据..."
    # time.sleep(2)
    result_data["reading_texts"] = []
    print(image_flag, video_flag)

    if image_flag:
        for image in result_data["page_images"]:
            result_data["reading_texts"].append(process_ocr(os.path.join(get_output_dir(), image)))
    if video_flag:
        for video in result_data["page_videos"]:
            result_data["reading_texts"].append(video_main(os.path.join(get_output_dir(), video)))

    progress["step"] = 50


def Analysising():
    """模拟分析阶段"""
    progress["message"] = "正在进行情绪与热度分析..."
    time.sleep(2)
    result_data["analysing_imgs"] = ["analysising.png"]
    progress["step"] = 75


def Picturing():
    """模拟绘图阶段"""
    progress["message"] = "正在绘制用户画像..."
    # time.sleep(2)
    result_data["picturing_texts"].append(get_weibo_users_pic(picture_users_list))
    result_data["picturing_imgs"] = ["picturing.png"]
    progress["step"] = 100
    progress["message"] = "分析完成！"


def Run(keyword):
    global progress, result_data
    progress = {"status": "running", "step": 0, "message": "任务开始"}
    result_data = {
        "keyword": keyword,
        "screenshot": None,
        "page_text": [],
        "page_images": [],
        "page_videos": [],
        "reading_texts": [],
        "analysing_imgs": [],
        "picturing_texts": [],
        "picturing_imgs": []
    }
    global video_flag, image_flag
    video_flag = False
    image_flag = False

    Spidering()
    Reading()
    Analysising()
    Picturing()
    progress["status"] = "done"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run():
    keyword = request.form.get('keyword')

    # 根据搜索框更改.env文件
    update_env_file('WID', keyword)

    threading.Thread(target=Run, args=(keyword,)).start()
    return jsonify({"message": f"任务已开始：{keyword}"})

def update_env_file(key, value):
    """根据搜索框输入更新.env文件"""
    if value.startswith("http"):
        value = value.split('/')[-1]
        # print(value)
        # 如果是mid（16位）转化为wid（9位）
        if len(value) == 16:
            get_dict()
            value = mid_to_wid(value)
        print(value)

    if value:
        set_key(dotenv_path, key, value)
        print(f"已更新 {key} 为 {value}")

def get_wid_from_env():
    """从 .env 文件中读取 WID 的值"""
    config = dotenv_values(dotenv_path)  # 获取所有配置的键值对
    wid = config.get('WID')  # 获取 WID 的值
    return wid

@app.route('/progress')
def get_progress():
    return jsonify(progress)


@app.route('/result')
def result():
    if progress["status"] != "done":
        return redirect(url_for('index'))
    return render_template('result.html', result=result_data)


if __name__ == '__main__':
    app.run(debug=True, port=8080)

