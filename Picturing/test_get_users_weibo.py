import logging
import os.path
import warnings

import openpyxl
import requests
import torch
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from collections import deque
import re
import ssl
import jieba
import time
import chardet
import random
import urllib3
from playwright.sync_api import sync_playwright

import sys
import io
from datetime import datetime, timedelta
import pandas as pd

from webencodings import iter_encode
from win32trace import flush

from Spidering.backend.WeiboDeepAnalyzer import _read_env_value

warnings.filterwarnings("ignore", category=FutureWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4   # <-- the key part here, OP_LEGACY_SERVER_CONNECT
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

def parse_cookies(cookie_str):
    """把 cookies 字符串转成字典"""
    cookies = {}
    for item in cookie_str.split('; '):
        key, value = item.split('=', 1)
        cookies[key] = value
    return cookies

def get_html_static(i_url, max_retries, timeout, wait_time):
    i_headers_list = [
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
        'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
        'Opera/9.25 (Windows NT 5.1; U; en)',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
        'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
        'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
        'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
        "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "]

    i_cookies_str = _read_env_value('COOKIE')# "SCF=ArIEu7iUff9L_s_UHqg7jALo0ivGgoTXt0GAMqI1LQQPLNC7HSWLyB4jjDXG-CSVuntLZWY8Y9Tl9eX01Q5OCtE.; SUB=_2A25FC0A9DeRhGeBP7lUV9irJyTSIHXVmad31rDV6PUJbktAYLWHikW1NRVJY2nlZSW07uY15Pl7_xdrA6LWXwo2Y; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFFQca6vuqgUIBYuZrW5rGM5NHD95QceK-NShqXSKzRWs4Dqcjdi--Xi-iWiKLWi--ciK.RiKLsi--ciKL8iKnp; SSOLoginState=1745825901; ALF=1748417901; _T_WM=45814674305; MLOGIN=1"
    i_cookies = parse_cookies(i_cookies_str)

    i_html = b''
    i_encoding = 'utf-8'
    for attempt in range(max_retries):
        i_response = None
        # 随机使用headers列表中的某个header
        i_headers = {"User-Agent": random.choice(i_headers_list),
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                     "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                     "Connection": "keep-alive",
                     "Referer": "https://www.bing.com/", }
        try:
            # Requests库请求访问网页
            i_response = requests.get(url=i_url,
                                      headers=i_headers,
                                      timeout=timeout,
                                      verify=False,
                                      stream=True,
                                      cookies=i_cookies)
            i_response.raise_for_status()

            # 获取网页编码格式
            i_encoding = chardet.detect(i_response.content)['encoding']
            if i_encoding is None:
                i_encoding = i_response.apparent_encoding
                if i_encoding is None:
                    i_encoding = 'utf-8'

            i_response.encoding = i_encoding # i_response.encoding = 'utf-8'

            # 获取网页文本内容
            i_html = i_response.content.decode('utf-8', errors='replace')
            # i_logger.info("Successfully Get Respond from Url", i_url)

            return i_html, i_encoding

        except requests.exceptions.HTTPError as e:
            # print(f"Error {e.response.status_code}: Can't Get Respond from Url {i_url}")
            print(f"Get Html Static - {e.response.status_code}: Can't Get Respond from Url {i_url}")

            if e.response.status_code == 404 or e.response.status_code == 403:  # 404/403 code abandon
                return i_html, i_encoding # 网页反馈404（不存在）或403（无权限）时没必要再次尝试爬取
            elif e.response.status_code == 412 or e.response.status_code == 432:
                print("Try Dynamic")
                i_html, i_encoding = get_html_dynamic(i_url)
                return i_html, i_encoding
            else:
                time.sleep(random.uniform(0.005, wait_time))
        except requests.exceptions.RequestException as ei:
            # print(f"Error {ei}: Can't Get Respond from Url {i_url}")
            print(f"Get Html Static - {ei}: Can't Get Respond from Url {i_url}")
            if "UNSAFE_LEGACY_RENEGOTIATION_DISABLED" in str(ei):
                print("Try Mount")
                with requests.session() as s:
                    s.mount("https://", TLSAdapter())
                    s.headers.update(i_headers)
                    try:
                        i_html = s.get(i_url).content.decode('utf-8', errors='replace')
                        return i_html
                    except requests.exceptions.ConnectionError as eii:
                        print(f"Get Html Static - {eii}: Can't Get Respond from Url {i_url}")

            time.sleep(random.uniform(0.005, wait_time))
        finally:
            if i_response is not None:
                i_response.close()
            time.sleep(random.uniform(0.005, wait_time))

        # print(f"Error: Can't Get Response from Url {i_url}")

        return i_html, i_encoding

def get_html_dynamic(i_url):
    i_html = b''
    i_encoding = 'utf-8'
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 打开目标网页
            page.goto(i_url, timeout=2000) # 设置超时时间为3秒

            # 等待页面完全加载
            page.wait_for_load_state("networkidle")  # 等待网络空闲
            page.wait_for_load_state("domcontentloaded")  # 等待 DOM 内容加载完成

            # 获取页面的完整 HTML 内容
            i_html = page.content()
        except TimeoutError:
            print(f"Get Html Dynamic - Timeout: Can't Get Respond from Url {i_url}")
            i_html = page.content()
        except Exception as e:
            print(f"Get Html Dynamic - {e}: Can't Get Respond from Url {i_url}")

        # 关闭浏览器
        browser.close()
    return i_html, i_encoding

def standardize_time(time_str):
    """
    将微博时间标准化为datetime对象
    """
    try:
        # print(time_str, flush=True)
        if "刚刚" in time_str:
            return datetime.now()
        elif "分钟" in time_str:
            minutes = int(re.search(r'(\d+)', time_str).group(1))
            return datetime.now() - pd.to_timedelta(f'{minutes}m')
        elif "小时" in time_str:
            hours = int(re.search(r'(\d+)', time_str).group(1))
            return datetime.now() - pd.to_timedelta(f'{hours}h')
        elif "今天" in time_str:
            clock_time = time_str.split(' ')[-1]
            return datetime.strptime(f"{datetime.now().strftime('%Y-%m-%d')} {clock_time}", '%Y-%m-%d %H:%M')
        elif "昨天" in time_str:
            today = datetime.now()
            yesterday = today - pd.to_timedelta('1d')
            return datetime.strptime(f"{yesterday.strftime('%Y-%m-%d')} {time_str.split(' ')[-1]}", '%Y-%m-%d %H:%M')
            # 新增处理 "04-29 10:01" 这种格式
        elif re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', time_str):
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        elif re.match(r'\d{2}月\d{2}日 \d{2}:\d{2}', time_str):
            year = datetime.now().year
            time_str_clean = time_str.replace("月", "-").replace("日", "")
            return datetime.strptime(f"{year}-{time_str_clean}", '%Y-%m-%d %H:%M')
        else:
            return None
    except Exception as e:
        print(f"标准化时间出错: {e}")
        return None

def save_weibo(i_created_at, i_content, i_weibo_id, i_weibo_url):
    year = str(i_created_at.year)
    month = str(i_created_at.month).zfill(2)
    day = str(i_created_at.day).zfill(2)

    save_dir = os.path.join("./Output", year, month, day)
    os.makedirs(save_dir, exist_ok=True)

    # filename = f"{dt.strftime('%Y%m%d_%H%M%S')}_{weibo_info['id']}.txt"
    match = re.search(r'【(.*?)】', i_content)
    if match:
        filename_part = match.group(1).strip()
    else:
        filename_part = f"微博_{i_weibo_id}"
    # 去除文件名中非法字符（如 Windows 不允许的符号）
    filename_part = re.sub(r'[\/:*?"<>|]', '_', filename_part)
    filename = f"{filename_part}.txt"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"发布时间：{i_created_at}\n")
        f.write(f"文章id：{i_weibo_id}\n")
        f.write(f"来源：{i_weibo_url}\n")
        f.write(f"内容：\n{i_content}\n")

    return "saved"

total_count = 0
def parse_content(i_card, i_encoding, start_time, end_time):
    # print(i_card)
    i_id = i_card.get('id')
    # print(i_id)
    if i_id is None:
        print("不合条件*1", flush=True)
        return 0
    i_links = i_card.find_all('a')
    for i_link in i_links:
        i_href = i_link.get('href')
        if "/comment/" in i_href:
            i_href = urljoin("https://weibo.cn", i_href)
            # print(i_href)
            i_html, i_encoding = get_html_static(i_href, 2, 2, 0.01)
            i_soup = BeautifulSoup(i_html, features="html.parser")
            i_content = i_soup.find_all('span', class_='ctt')
            i_time = i_soup.find_all('span', class_='ct')
            print(i_time[0].get_text(strip=True), flush=True)

            i_created_at = standardize_time(i_time[0].get_text(strip=True))
            print(i_created_at, flush=True)

            if i_created_at < start_time:
                return 1
            if i_created_at > end_time:
                # time.sleep(random.randint(1, 3))
                print("非所需时间微博*1")
                return 0

            save_weibo(i_created_at, i_content[0].get_text(), i_id, i_href)

            global total_count
            total_count += 1
            time.sleep(random.randint(1, 2))
            print(f"爬取微博数*1，id:{i_id}，时间{i_created_at}， 防封暂停1~2秒", flush=True)

            if total_count % 50 == 0:
                sleep_time = random.randint(5, 10)
                print(
                    f"已爬取{total_count}条，最新微博时间为{i_created_at}，休息{sleep_time}秒防封...", flush=True)
                time.sleep(sleep_time)

            return 0
    return 0

def parse_card(i_html, i_url, i_encoding):
    i_news = []
    i_soup = BeautifulSoup(i_html, features="html.parser")
    i_cards = i_soup.find_all('div', class_='c')
    return i_cards



if __name__ == '__main__':

    i_user_id = "5238869367" # "5044281310" # [5238869367,7904512652,7756485110,7756485110,5546364752]
    i_url = f"https://weibo.cn/{i_user_id}/profile?page=1"
    print("获取总页数...", flush=True)
    i_html, i_encoding = get_html_static(i_url, 2, 2, 0.01)
    # <input name="mp" type="hidden" value="16752" />
    i_soup = BeautifulSoup(i_html, features="html.parser")
    i_pages = (i_soup.find('input', attrs={'name': 'mp', 'type': 'hidden'})).get('value')
    print(f"所有微博共{i_pages}页", flush=True)

    # start_date = "2024-04-01 0:00"
    # end_date = "2025-04-29 0:00"
    # 获取当前时间和前一天时间
    end_date_dt = datetime.now()
    start_date_dt = end_date_dt - timedelta(days=1)
    # 格式化为原来使用的 "%Y-%m-%d %H:%M" 格式
    start_date = start_date_dt.strftime("%Y-%m-%d %H:%M")
    end_date = end_date_dt.strftime("%Y-%m-%d %H:%M")

    print(f"开始爬取用户 {i_user_id} 从 {start_date} 到 {end_date} 期间的微博...", flush=True)  # 共 {pages} 页")

    start_time = datetime.strptime(start_date, "%Y-%m-%d %H:%M") if start_date else None
    end_time = datetime.strptime(end_date, "%Y-%m-%d %H:%M") if end_date else None


    for i_page in range(1, int(i_pages) + 1): # (1612, int(i_pages) + 1)
        i_weibo_url = f"https://weibo.cn/{i_user_id}/profile?page={i_page}"
        print(i_weibo_url, flush=True)
        i_html, i_encoding = get_html_static(i_weibo_url, 2, 2, 0.01)
        i_cards = parse_card(i_html, i_weibo_url, i_encoding)
        finish = 0
        for i_card in i_cards:
            finish = parse_content(i_card, i_encoding, start_time, end_time)
            if finish == 1:
                break
        time.sleep(random.randint(4, 5))  # 常规延迟
        print("爬取微博页数*1, 防封暂停4~5秒", flush=True)
        if finish == 1:
            break
    print("========================================", flush=True)
    print(f"已完成爬取微博共{total_count}条", flush=True)


