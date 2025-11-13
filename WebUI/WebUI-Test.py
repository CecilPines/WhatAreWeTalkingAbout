from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import sys

# 将项目根目录添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Flask 实例化时配置静态文件夹
app = Flask(__name__,template_folder=os.path.join(os.path.dirname(__file__), 'WebUI', 'templates'))

import threading
import time
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
    # 检查分析是否成功
    if not analyzer.analyze():  # max_comment_pages和max_repost_pages从.env读取
        progress["message"] = "爬取失败：无法获取微博内容"
        progress["step"] = 0
        return
    
    # 获取wid
    wid = get_wid_from_env()
    # time.sleep(2)

    result_data["screenshot"] = "screenshot.png"

    spidering_result_path = os.path.join(get_project_root(), "Spidering", "backend", "weibo_analysis", wid)
    
    # 检查文件是否存在
    weibo_file = os.path.join(spidering_result_path, wid+"_weibo.csv")
    comments_file = os.path.join(spidering_result_path, wid+"_comments.csv")
    reposts_file = os.path.join(spidering_result_path, wid+"_reposts.csv")
    
    if not os.path.exists(weibo_file):
        progress["message"] = f"错误：找不到文件 {weibo_file}"
        progress["step"] = 0
        return
    
    # 读取CSV文件，如果文件不存在则创建空的DataFrame
    try:
        df_weibo = pandas.read_csv(weibo_file, encoding='utf-8')
    except FileNotFoundError:
        df_weibo = pandas.DataFrame()
        print(f"警告：文件 {weibo_file} 不存在，使用空DataFrame")
    
    try:
        df_comments = pandas.read_csv(comments_file, encoding='utf-8') if os.path.exists(comments_file) else pandas.DataFrame()
    except Exception as e:
        df_comments = pandas.DataFrame()
        print(f"警告：读取评论文件失败: {e}")
    
    try:
        df_repost = pandas.read_csv(reposts_file, encoding='utf-8') if os.path.exists(reposts_file) else pandas.DataFrame()
    except Exception as e:
        df_repost = pandas.DataFrame()
        print(f"警告：读取转发文件失败: {e}")

    result_data["page_text"] = []
    # 安全地添加微博内容
    if not df_weibo.empty:
        for index, row in df_weibo.iterrows():
            result_data["page_text"].append(row.tolist())
    # 安全地添加评论内容
    if not df_comments.empty:
        for index, row in df_comments.iterrows():
            result_data["page_text"].append(row.tolist())

    global picture_users_list
    # 安全地提取评论者ID和转发者ID
    if not df_comments.empty and '评论者ID' in df_comments.columns:
        picture_users_list += df_comments['评论者ID'].tolist()
    if not df_repost.empty and '转发者ID' in df_repost.columns:
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

    """直接使用 WeiboDeepAnalyzer 已下载的视频文件"""
    result_data["page_videos"] = []
    # 从 get_output_dir() 目录中查找 WeiboDeepAnalyzer 下载的视频文件
    # 视频文件名格式：{wid}_{idx}.mp4
    output_dir = get_output_dir()
    if os.path.exists(output_dir):
        # 遍历目录中的文件，查找以 wid 开头且以视频扩展名结尾的文件
        video_extensions = ['.mp4', '.m3u8', '.flv']
        for filename in os.listdir(output_dir):
            if filename.startswith(wid) and any(filename.lower().endswith(ext) for ext in video_extensions):
                result_data["page_videos"].append(filename)
                print(f"找到视频文件: {filename}")
    
    if result_data["page_videos"]:
        video_flag = True
        print(f"共找到 {len(result_data['page_videos'])} 个视频文件")
    else:
        print("未找到视频文件（可能未启用视频下载功能）")

    progress["step"] = 25
    print(f"Spidering阶段完成，progress step: {progress['step']}")


def Reading():
    """模拟读取阶段"""
    progress["message"] = "正在读取微博数据..."
    # time.sleep(2)
    result_data["reading_texts"] = []
    print(f"Reading阶段开始 - image_flag: {image_flag}, video_flag: {video_flag}")

    try:
        if image_flag:
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
        
        if video_flag:
            print(f"开始处理 {len(result_data['page_videos'])} 个视频...")
            for video in result_data["page_videos"]:
                video_path = os.path.join(get_output_dir(), video)
                print(f"处理视频: {video_path}")
                try:
                    video_result = video_main(video_path)
                    result_data["reading_texts"].append(video_result)
                    print(f"视频 {video} 处理完成")
                except Exception as e:
                    print(f"处理视频 {video} 时出错: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"Reading阶段完成，共处理 {len(result_data['reading_texts'])} 个结果")
    except Exception as e:
        print(f"Reading阶段发生错误: {e}")
        import traceback
        traceback.print_exc()

    progress["step"] = 50
    print(f"Reading阶段结束，progress step: {progress['step']}")


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

    try:
        print("=" * 80)
        print("开始执行任务流程...")
        print("=" * 80)
        
        print("\n[1/2] 执行 Spidering 阶段...")
        Spidering()
        print(f"Spidering 完成，progress step: {progress['step']}, status: {progress['status']}")
        
        print("\n[2/2] 执行 Reading 阶段...")
        Reading()
        print(f"Reading 完成，progress step: {progress['step']}, status: {progress['status']}")
        
        Analysising()
        # Picturing()
        
        print("\n" + "=" * 80)
        print("所有阶段执行完成，设置 status 为 done")
        print("=" * 80)
        progress["status"] = "done"
        progress["message"] = "分析完成！"
        print(f"最终状态 - status: {progress['status']}, step: {progress['step']}, message: {progress['message']}")
        
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        progress["status"] = "done"
        progress["message"] = f"执行完成（有错误: {str(e)}）"
        print(f"错误处理后状态 - status: {progress['status']}, step: {progress['step']}")


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

