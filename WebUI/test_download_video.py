from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import requests
import os

from GetOutput import get_output_dir

def download_video(video_url, output_path):
    """下载视频并保存到指定路径"""
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"视频已下载到 {output_path}")
    else:
        print(f"下载失败，HTTP 状态码: {response.status_code}")


def get_video_url(page_url):
    """使用 Selenium 获取视频页面中的视频 URL"""
    # 配置 WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # 设置 WebDriver 路径
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(page_url)  # 访问微博视频页面
        time.sleep(5)  # 等待页面加载

        # 找到视频标签并提取视频源 URL
        video_element = driver.find_element(By.TAG_NAME, "video")
        video_url = video_element.get_attribute("src")  # 获取视频源 URL

        if video_url:
            return video_url
        else:
            print("未能找到视频 URL")
            return None
    finally:
        driver.quit()


if __name__ == "__main__":
    # 设置微博页面 URL
    page_url = "https://m.weibo.cn/s/video/show?object_id=1034%3A5229952417595397&fromWap=1"

    # 获取视频的真实 URL
    video_url = get_video_url(page_url)

    if video_url:
        # 设置保存路径
        output_path = os.path.join(get_output_dir(), "weibo_video.mp4")
        # 下载视频
        download_video(video_url, output_path)
