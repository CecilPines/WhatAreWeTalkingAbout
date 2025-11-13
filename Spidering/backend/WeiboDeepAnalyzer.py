# -*- coding: utf-8 -*-
# 作者:             基于现有代码重构
# 创建时间:          2025/10/29
# 运行环境:          Python 3.6+
# 文件说明:          单条微博深度分析工具 - 整合内容、评论、转发的完整分析

import csv
import os
import re
import json
import time
import random
import traceback
from datetime import datetime, timedelta
from collections import OrderedDict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from GetOutput import get_output_dir
import requests
from lxml import etree

requests.packages.urllib3.disable_warnings()

# global cookies

def _read_env_value(key: str):
    """
    从环境变量或.env文件读取指定键的值
    
    Args:
        key: 环境变量键名
    
    Returns:
        str: 环境变量的值，如果不存在则返回空字符串
    """
    # 优先从环境变量读取
    env_value = os.environ.get(key)
    if env_value:
        return env_value
    
    # 从.env文件读取（从项目根目录）
    # 由于此文件在backend/目录下，需要向上两级目录到达项目根目录
    project_root = os.path.dirname(os.path.dirname(__file__))
    # print(project_root)
    env_path = os.path.join(project_root, '.env')
    # env_path = "../.env"
    # print(f"Done-{env_path}")
    try:
        with open(env_path, 'r', encoding='utf-8', errors="ignore") as f:
            # print("Open")
            # print(f.read())
            for raw_line in f:
                # print(raw_line)
                line = raw_line.strip()
                # print(line)
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    # print(line)
                    file_key, value = line.split('=', 1)
                    print(file_key, value)
                    if file_key.strip() == key:
                        return value.strip().strip('"').strip("'")
    except Exception:
        print("Open .env file Done-Error")
        pass
    return ''


def _read_cookie_from_env_file():
    """从环境变量或.env文件读取Cookie"""
    return _read_env_value('COOKIE')


def _read_wid_from_env_file():
    """从环境变量或.env文件读取微博ID"""
    return _read_env_value('WID')


def _read_int_env_value(key: str, default=None):
    """
    从环境变量或.env文件读取整数类型的值
    
    Args:
        key: 环境变量键名
        default: 默认值（如果未找到或转换失败）
    
    Returns:
        int: 整数值，如果未找到或转换失败则返回default
    """
    value = _read_env_value(key)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _read_bool_env_value(key: str, default=False):
    """
    从环境变量或.env文件读取布尔类型的值
    
    Args:
        key: 环境变量键名
        default: 默认值（如果未找到）
    
    Returns:
        bool: 布尔值
    """
    value = _read_env_value(key)
    if not value:
        return default
    # 支持多种布尔值表示方式
    value_lower = value.lower().strip()
    if value_lower in ('true', '1', 'yes', 'on', 'enabled'):
        return True
    elif value_lower in ('false', '0', 'no', 'off', 'disabled'):
        return False
    return default


class WeiboDeepAnalyzer:
    """
    单条微博深度分析器
    
    功能：
    1. 提取微博完整内容（文字、图片、视频等）
    2. 爬取所有评论及回复层级
    3. 爬取所有转发信息
    4. 生成互动统计分析
    5. 输出结构化数据（JSON + CSV）
    """
    
    def __init__(self, wid=None, cookie=None, output_dir=None, download_images=None, download_videos=None):
        """
        初始化分析器
        
        Args:
            wid: 微博ID（可以是数字ID或mid，可选，如果未提供则从环境变量或.env文件读取）
            cookie: 微博Cookie（可选，如果未提供则从环境变量或.env文件读取）
            output_dir: 输出目录（可选，如果未提供则从环境变量或.env文件读取，默认'weibo_analysis'）
            download_images: 是否下载图片到本地（可选，如果未提供则从环境变量或.env文件读取，默认False）
            download_videos: 是否下载视频到本地（可选，如果未提供则从环境变量或.env文件读取，默认False）
        """
        # 如果未提供wid，尝试从环境变量或.env文件读取
        if wid is None:
            wid = _read_wid_from_env_file()
        
        # 验证wid参数
        if not wid or not isinstance(wid, str):
            raise ValueError('微博ID不能为空，请提供有效的微博ID或在.env文件中设置WID')
        
        wid = wid.strip()
        if not wid:
            raise ValueError('微博ID不能为空，请提供有效的微博ID或在.env文件中设置WID')
        
        # 检查是否是无效的占位符值
        invalid_values = ['string', 'wid', '微博ID', 'weibo_id', 'id']
        if wid.lower() in [x.lower() for x in invalid_values]:
            raise ValueError(f'微博ID不能是占位符值 "{wid}"，请输入真实的微博ID（例如：QbelLys5Z）')
        
        self.wid = wid
        self.cookie = cookie if cookie else _read_cookie_from_env_file()
        # global cookies
        # cookies = self.cookie
        
        # 如果未提供download_images，从环境变量读取
        if download_images is None:
            self.download_images = _read_bool_env_value('DOWNLOAD_IMAGES', default=False)
        else:
            self.download_images = download_images
        
        # 如果未提供download_videos，从环境变量读取
        if download_videos is None:
            self.download_videos = _read_bool_env_value('DOWNLOAD_VIDEOS', default=False)
        else:
            self.download_videos = download_videos
        
        # 如果未提供output_dir，从环境变量读取
        if output_dir is None:
            output_dir = _read_env_value('OUTPUT_DIR')
            if not output_dir:
                output_dir = 'weibo_analysis'
        
        if not self.cookie:
            raise Exception('COOKIE 为空，请配置环境变量或 .env 文件中的 COOKIE')
        
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 使用Session并关闭代理
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(self.headers)
        
        # 输出目录设置
        self.output_dir = os.path.join(os.path.dirname(__file__), output_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.wid_dir = os.path.join(self.output_dir, self.wid)
        if not os.path.exists(self.wid_dir):
            os.makedirs(self.wid_dir)
        
        # 图片保存目录
        if self.download_images:
            self.images_dir = os.path.join(self.wid_dir, 'images')
            if not os.path.exists(self.images_dir):
                os.makedirs(self.images_dir)
        
        # 视频保存目录
        if self.download_videos:
            self.videos_dir = os.path.join(self.wid_dir, 'videos')
            if not os.path.exists(self.videos_dir):
                os.makedirs(self.videos_dir)
        
        # 数据存储
        self.weibo_data = {}
        self.comments_data = []
        self.reposts_data = []
        self.stats = {}
        
        print(f'微博深度分析器初始化完成')
        print(f'目标微博ID: {self.wid}')
        print(f'输出目录: {self.wid_dir}')
        if self.download_images:
            print(f'图片下载: 启用 -> {self.images_dir}')
        else:
            print(f'图片下载: 禁用')
        if self.download_videos:
            # 视频实际保存到 get_output_dir()，与 test_download_video.py 一致
            video_output_dir = get_output_dir()
            print(f'视频下载: 启用 -> {video_output_dir}')
        else:
            print(f'视频下载: 禁用')
        print('=' * 80)
    
    def _request(self, url, timeout=10, retry=3):
        """统一的HTTP请求处理"""
        for attempt in range(retry):
            try:
                res = self.session.get(url, timeout=timeout, verify=False)
                if res.status_code == 200 and res.content:
                    return res
                else:
                    print(f'HTTP {res.status_code} - {url}')
            except Exception as e:
                print(f'请求失败 (尝试 {attempt + 1}/{retry}): {e}')
                if attempt < retry - 1:
                    time.sleep(2)
        return None
    
    def _parse_html(self, url):
        """解析HTML页面"""
        res = self._request(url)
        if res is None:
            return None
        try:
            selector = etree.HTML(res.content)
            return selector
        except Exception as e:
            print(f'HTML解析失败: {e}')
            return None
    
    def _parse_time(self, time_str):
        """解析时间字符串为标准格式"""
        try:
            time_str = time_str.split('来自')[0].strip()
            
            if '刚刚' in time_str:
                return datetime.now().strftime('%Y-%m-%d %H:%M')
            elif '分钟' in time_str:
                minute = int(re.search(r'(\d+)分钟', time_str).group(1))
                return (datetime.now() - timedelta(minutes=minute)).strftime('%Y-%m-%d %H:%M')
            elif '小时' in time_str:
                hour = int(re.search(r'(\d+)小时', time_str).group(1))
                return (datetime.now() - timedelta(hours=hour)).strftime('%Y-%m-%d %H:%M')
            elif '今天' in time_str:
                today = datetime.now().strftime('%Y-%m-%d')
                time_part = time_str.replace('今天', '').strip()
                return f'{today} {time_part}'
            elif '月' in time_str and '日' in time_str:
                year = datetime.now().strftime('%Y')
                match = re.search(r'(\d{1,2})月(\d{1,2})日\s*(\d{1,2}:\d{2})?', time_str)
                if match:
                    month = match.group(1).zfill(2)
                    day = match.group(2).zfill(2)
                    time_part = match.group(3) if match.group(3) else '00:00'
                    return f'{year}-{month}-{day} {time_part}'
            else:
                # 尝试直接解析完整日期
                if len(time_str) >= 16:
                    return time_str[:16]
            
            return time_str
        except Exception as e:
            print(f'时间解析失败: {e} - {time_str}')
            return time_str
    
    def _clean_text(self, text):
        """清理文本中的多余空白和特殊字符"""
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\u200b', '').strip()
        return text
    
    def _get_weibo_from_mobile(self, weibo_id):
        """
        从 m.weibo.cn 获取完整微博信息（包括图片和视频）
        参考 weibo.py 的 get_long_weibo() 方法实现
        
        Args:
            weibo_id: 微博ID（可以是mid如'QbelLys5Z'或数字id）
        
        Returns:
            dict: 包含完整图片和视频信息的字典，格式：
                {
                    'images': [图片URL列表],
                    'videos': [视频URL列表],
                    'live_photos': [Live Photo URL列表]
                }
            如果失败返回None
        """
        url = f"https://m.weibo.cn/detail/{weibo_id}"
        try:
            print(f'    正在访问: {url}')
            response = self.session.get(url, headers=self.headers, verify=False, timeout=15)
            if response.status_code != 200:
                print(f'    访问失败: HTTP {response.status_code}')
                return None
            
            html = response.text
            
            # 查找JSON数据（参考 weibo.py 的实现）
            status_start = html.find('"status":')
            if status_start == -1:
                print('    未找到 "status" JSON数据')
                return None
            
            html = html[status_start:]
            # 查找结束位置
            call_end = html.rfind('"call"')
            if call_end == -1:
                # 如果找不到 "call"，尝试其他方法
                # 查找最后一个大括号
                last_brace = html.rfind('}')
                if last_brace == -1:
                    print('    无法确定JSON结束位置')
                    return None
                html = html[:last_brace + 1]
            else:
                html = html[:call_end]
                html = html[:html.rfind(",")]
                html = "{" + html + "}"
            
            try:
                js = json.loads(html, strict=False)
            except json.JSONDecodeError as e:
                print(f'    JSON解析失败: {e}')
                return None
            
            weibo_info = js.get("status")
            if not weibo_info:
                print('    未找到 status 数据')
                return None
            
            # 提取图片
            images = []
            if weibo_info.get("pics"):
                for pic in weibo_info["pics"]:
                    if pic.get("large") and pic["large"].get("url"):
                        images.append(pic["large"]["url"])
                    elif pic.get("url"):
                        # 备用：如果没有large，使用url
                        images.append(pic["url"])
            
            # 提取视频
            videos = []
            if weibo_info.get("page_info"):
                page_info = weibo_info["page_info"]
                if page_info.get("type") == "video":
                    media_info = page_info.get("urls") or page_info.get("media_info")
                    if media_info:
                        # 按优先级获取视频URL（参考 weibo.py 的 get_video_url 方法）
                        video_url = (media_info.get("mp4_720p_mp4") or
                                   media_info.get("mp4_hd_url") or
                                   media_info.get("hevc_mp4_hd") or
                                   media_info.get("mp4_sd_url") or
                                   media_info.get("mp4_ld_mp4") or
                                   media_info.get("stream_url_hd") or
                                   media_info.get("stream_url"))
                        if video_url:
                            videos.append(video_url)
            
            # 提取Live Photo
            live_photos = []
            if weibo_info.get("live_photo"):
                live_photo_list = weibo_info["live_photo"]
                if isinstance(live_photo_list, list):
                    live_photos = live_photo_list
                elif isinstance(live_photo_list, str):
                    live_photos = [live_photo_list]
            
            result = {
                'images': images,
                'videos': videos,
                'live_photos': live_photos
            }
            
            print(f'    成功提取: {len(images)} 张图片, {len(videos)} 个视频, {len(live_photos)} 个Live Photo')
            return result
            
        except Exception as e:
            print(f'    从 m.weibo.cn 获取信息失败: {e}')
            traceback.print_exc()
            return None
    
    def _download_image(self, img_url, save_path):
        """
        下载单张图片
        
        Args:
            img_url: 图片URL
            save_path: 保存路径
        
        Returns:
            bool: 是否下载成功
        """
        if os.path.exists(save_path):
            print(f'  图片已存在: {os.path.basename(save_path)}')
            return True
        
        try:
            print(f'  正在下载: {os.path.basename(save_path)}...', end=' ')
            
            # 添加Referer头解决403防盗链问题
            download_headers = self.headers.copy()
            download_headers['Referer'] = 'https://weibo.cn/'
            download_headers['Accept'] = 'image/webp,image/apng,image/*,*/*;q=0.8'
            download_headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
            
            # 使用带Referer的headers下载
            response = self.session.get(img_url, headers=download_headers, timeout=20, verify=False)
            
            if response.status_code == 200 and response.content:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print('✓')
                time.sleep(0.5)
                return True
            elif response.status_code == 403:
                # 如果403，尝试不使用Cookie下载
                print('(403)尝试无Cookie下载...', end=' ')
                simple_headers = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': 'https://weibo.cn/'
                }
                retry_response = self.session.get(img_url, headers=simple_headers, timeout=20, verify=False)
                if retry_response.status_code == 200 and retry_response.content:
                    with open(save_path, 'wb') as f:
                        f.write(retry_response.content)
                    print('✓')
                    time.sleep(0.5)
                    return True
                else:
                    print(f'✗ 失败 (HTTP {retry_response.status_code})')
                    return False
            else:
                print(f'✗ 下载失败 (HTTP {response.status_code})')
                return False
        except Exception as e:
            print(f'✗ 下载失败: {e}')
            return False
    
    def _download_video(self, video_url, output_path):
        """
        下载视频并保存到指定路径
        参考 test_download_video.py 的实现
        
        Args:
            video_url: 视频URL
            output_path: 保存路径
        
        Returns:
            bool: 是否下载成功
        """
        if os.path.exists(output_path):
            print(f'  视频已存在: {os.path.basename(output_path)}')
            return True
        
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"  视频已下载到 {output_path}")
                return True
            else:
                print(f"  下载失败，HTTP 状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"  下载失败: {e}")
            return False
    
    # ==================== 微博内容提取 ====================
    
    def get_weibo_screenshot(self):
        """
        获取微博页面截图
        :return: nothing
        """
        print('\n[0/4] 正在截图微博内容...')

        # 设置浏览器选项
        options = Options()
        options.headless = True  # 不显示浏览器界面（后台运行）

        # 使用 webdriver-manager 自动管理 ChromeDriver
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"使用 webdriver-manager 启动 Chrome 失败: {e}")
            print("尝试使用系统默认的 ChromeDriver...")
            # 如果 webdriver-manager 失败，尝试使用系统默认路径
            driver = webdriver.Chrome(options=options)
        url = f'https://weibo.cn/comment/{self.wid}'
        screenshot_path = os.path.join(get_output_dir(), "screenshot.png")

        try:
            # 打开网页
            driver.get(url)

            # 等待页面加载完成（你可以根据需要调整等待时间）
            time.sleep(3)  # 等待 3 秒，确保页面加载完毕

            # 截图并保存
            driver.save_screenshot(screenshot_path)
            print(f"截图已保存至 {screenshot_path}")
        except Exception as e:
            print(f"截图失败: {e}")
        finally:
            driver.quit()  # 关闭浏览器
        return None

    def get_weibo_content(self):
        """
        获取微博完整内容
        
        Returns:
            dict: 包含微博所有信息的字典
        """
        print('\n[1/4] 正在提取微博内容...')
        
        url = f'https://weibo.cn/comment/{self.wid}'
        selector = self._parse_html(url)
        
        if selector is None:
            print('❌ 无法访问微博页面，请检查 Cookie 是否有效')
            return None
        
        try:
            # 获取微博主体内容块
            weibo_block = selector.xpath("//div[@class='c'][@id]")[0]
            
            # 提取微博ID
            weibo_id = weibo_block.xpath('@id')[0]
            if weibo_id.startswith('M_'):
                weibo_id = weibo_id[2:]
            
            # 提取用户信息
            user_link = weibo_block.xpath('.//a[@class="nk"]/@href')
            user_name = weibo_block.xpath('.//a[@class="nk"]/text()')
            
            user_id = None
            if user_link:
                match = re.search(r'/(\d+)', user_link[0])
                if match:
                    user_id = match.group(1)
            
            # 提取微博内容
            content_spans = weibo_block.xpath('.//span[@class="ctt"]')
            content = ''
            if content_spans:
                content = self._clean_text(''.join(content_spans[0].xpath('string(.)')))
                # 移除开头的冒号
                if content.startswith(':'):
                    content = content[1:].strip()
            
            # 检查是否需要展开全文
            full_text_link = weibo_block.xpath('.//a[contains(text(), "全文")]/@href')
            full_selector = None  # 初始化变量
            if full_text_link:
                print('  检测到长微博，正在获取全文...')
                full_url = 'https://weibo.cn' + full_text_link[0]
                full_selector = self._parse_html(full_url)
                if full_selector:
                    full_content_div = full_selector.xpath("//div[@class='c'][@id]")[0]
                    full_content_span = full_content_div.xpath('.//span[@class="ctt"]')
                    if full_content_span:
                        content = self._clean_text(''.join(full_content_span[0].xpath('string(.)')))
                        if content.startswith(':'):
                            content = content[1:].strip()
                time.sleep(1)
            
            # 提取图片链接（使用测试成功的代码逻辑）
            images = []
            pic_links = weibo_block.xpath('.//a[contains(@href, "/mblog/picAll/")]/@href')
            if pic_links:
                print('  检测到图片，正在提取...')
                # 使用 ?rl=2 参数，参考 test_image_download.py 的成功实现
                pic_link = pic_links[0]
                if '?rl=' not in pic_link:
                    pic_url = 'https://weibo.cn' + pic_link + '?rl=2'
                else:
                    pic_url = 'https://weibo.cn' + pic_link
                pic_selector = self._parse_html(pic_url)
                if pic_selector:
                    # 提取所有图片URL（使用large尺寸）
                    img_srcs = pic_selector.xpath('//img/@src')
                    for img in img_srcs:
                        if 'sinaimg' in img:
                            # 替换为大图链接
                            large_img = img.replace('/thumb180/', '/large/').replace('/wap180/', '/large/')
                            images.append(large_img)
                    
                    print(f'  找到 {len(images)} 张图片')
                    
                    # 如果启用图片下载
                    if self.download_images and images:
                        print('  开始下载图片...')
                        for idx, img_url in enumerate(images, 1):
                            save_filename = f'{self.wid}_{idx}.jpg'
                            save_path = os.path.join(self.images_dir, save_filename)
                            self._download_image(img_url, save_path)
                            save_path = os.path.join(get_output_dir(), save_filename)
                            self._download_image(img_url, save_path)
                
                time.sleep(1)
            
            # 提取视频链接（只保留实际视频文件URL，不提取跳转链接）
            videos = []
            # 检测是否有视频提示（通过检查是否有视频跳转链接）
            video_links = weibo_block.xpath('.//span[@class="ctt"]//a[contains(@href, "m.weibo.cn/s/video/show")]/@href')
            has_video_hint = bool(video_links)
            
            # 如果全文页面也有视频链接提示
            if full_text_link and full_selector:
                full_video_links = full_selector.xpath('.//span[@class="ctt"]//a[contains(@href, "m.weibo.cn/s/video/show")]/@href')
                if full_video_links:
                    has_video_hint = True
            
            # 检查内容中是否有视频相关的关键词（用于检测同时有视频和图片的微博）
            content_lower = content.lower()
            video_keywords = ['视频', 'video', '查看视频', '播放视频']
            has_video_keyword = any(keyword in content_lower for keyword in video_keywords)
            
            # 如果检测到视频提示或关键词，或者有图片（可能同时有视频），都尝试从 m.weibo.cn 获取视频
            # 注意：即使没有明确提示，也尝试获取（因为有些微博可能同时有视频和图片）
            should_fetch_video = has_video_hint or has_video_keyword or len(images) > 0
            
            if should_fetch_video:
                if has_video_hint:
                    print('  检测到视频链接，正在从 m.weibo.cn 获取实际视频文件URL...')
                elif has_video_keyword:
                    print('  检测到视频关键词，正在从 m.weibo.cn 获取实际视频文件URL...')
                else:
                    print('  检测到图片，尝试从 m.weibo.cn 获取视频信息（可能同时包含视频）...')
                
                mobile_data = self._get_weibo_from_mobile(self.wid)
                if mobile_data:
                    mobile_videos = mobile_data.get('videos', [])
                    # 只保留实际视频文件URL（.mp4、.m3u8等），过滤掉跳转链接
                    actual_video_urls = [v for v in mobile_videos if any(ext in v.lower() for ext in ['.mp4', '.m3u8', '.flv', 'video.weibocdn.com'])]
                    videos.extend(actual_video_urls)
                    if videos:
                        print(f'  找到 {len(videos)} 个实际视频文件')
                    else:
                        if has_video_hint or has_video_keyword:
                            print('  未找到实际视频文件URL（可能视频已删除或无法访问）')
                        # 如果没有明确视频提示，不输出警告（因为可能确实没有视频）
            
            # 提取发布时间和来源
            time_source = weibo_block.xpath('.//span[@class="ct"]/text()')
            publish_time = ''
            publish_source = ''
            if time_source:
                time_source_text = time_source[0]
                publish_time = self._parse_time(time_source_text)
                if '来自' in time_source_text:
                    publish_source = time_source_text.split('来自')[1].strip()
            
            # 提取互动数据（点赞、转发、评论）
            # 优先从 weibo.cn/attitude/{wid} 页面获取（最准确）
            like_count = 0
            repost_count = 0
            comment_count = 0
            
            # 方法1：从 weibo.cn/attitude/{wid} 页面获取统计数据（最准确的方法）
            print('  正在获取统计数据...')
            attitude_url = f'https://weibo.cn/attitude/{self.wid}'
            attitude_selector = self._parse_html(attitude_url)
            
            if attitude_selector:
                # 查找 id="attitude" 的div
                attitude_div = attitude_selector.xpath('//div[@id="attitude"]')
                if attitude_div:
                    attitude_text = ''.join(attitude_div[0].xpath('string(.)'))
                    
                    # 提取转发数
                    repost_match = re.search(r'转发\[(\d+)\]', attitude_text)
                    if repost_match:
                        repost_count = int(repost_match.group(1))
                    
                    # 提取评论数
                    comment_match = re.search(r'评论\[(\d+)\]', attitude_text)
                    if comment_match:
                        comment_count = int(comment_match.group(1))
                    
                    # 提取点赞数（在<span class="pms">中）
                    like_match = re.search(r'赞\[(\d+)\]', attitude_text)
                    if like_match:
                        like_count = int(like_match.group(1))
                
                time.sleep(0.5)  # 短暂延时
            
            # 方法2：如果attitude页面没有找到，尝试从当前页面的id="attitude"div中查找
            if like_count == 0 or repost_count == 0 or comment_count == 0:
                attitude_div = selector.xpath('//div[@id="attitude"]')
                if attitude_div:
                    attitude_text = ''.join(attitude_div[0].xpath('string(.)'))
                    
                    if repost_count == 0:
                        repost_match = re.search(r'转发\[(\d+)\]', attitude_text)
                        if repost_match:
                            repost_count = int(repost_match.group(1))
                    
                    if comment_count == 0:
                        comment_match = re.search(r'评论\[(\d+)\]', attitude_text)
                        if comment_match:
                            comment_count = int(comment_match.group(1))
                    
                    if like_count == 0:
                        like_match = re.search(r'赞\[(\d+)\]', attitude_text)
                        if like_match:
                            like_count = int(like_match.group(1))
            
            # 方法3：如果上述方法都失败，从weibo_block中查找（备用方法）
            if like_count == 0 or repost_count == 0 or comment_count == 0:
                # 从链接文本中提取
                like_links = weibo_block.xpath('.//a[contains(@href, "/attitude/")]//text()')
                for text in like_links:
                    match = re.search(r'赞\[(\d+)\]', text)
                    if match:
                        like_count = int(match.group(1))
                        break
                
                if repost_count == 0:
                    repost_links = weibo_block.xpath('.//a[contains(@href, "/repost/")]//text()')
                    for text in repost_links:
                        match = re.search(r'转发\[(\d+)\]', text)
                        if match:
                            repost_count = int(match.group(1))
                            break
                
                if comment_count == 0:
                    comment_links = weibo_block.xpath('.//a[contains(@href, "/comment/")]//text()')
                    for text in comment_links:
                        match = re.search(r'评论\[(\d+)\]', text)
                        if match:
                            comment_count = int(match.group(1))
                            break
                    
                    # 评论数可能在<span class="pms">中
                    if comment_count == 0:
                        comment_spans = weibo_block.xpath('.//span[@class="pms"]//text()')
                        for text in comment_spans:
                            match = re.search(r'评论\[(\d+)\]', text)
                            if match:
                                comment_count = int(match.group(1))
                                break
            
            # 方法4：如果上述方法都失败，使用footer_text作为最后的备用
            if like_count == 0 or repost_count == 0 or comment_count == 0:
                footer_text = ''.join(weibo_block.xpath('.//div[last()]//text()'))
                
                if like_count == 0:
                    like_match = re.search(r'赞\[(\d+)\]', footer_text)
                    if like_match:
                        like_count = int(like_match.group(1))
                
                if repost_count == 0:
                    repost_match = re.search(r'转发\[(\d+)\]', footer_text)
                    if repost_match:
                        repost_count = int(repost_match.group(1))
                
                if comment_count == 0:
                    comment_match = re.search(r'评论\[(\d+)\]', footer_text)
                    if comment_match:
                        comment_count = int(comment_match.group(1))
            
            # 检测是否需要从 m.weibo.cn 补充获取完整媒体信息
            # 情况：既有视频又有图片的微博，weibo.cn可能只显示跳转链接
            need_supplement = False
            
            # 情况1：如果图片数为0，尝试从 m.weibo.cn 获取（weibo.cn可能不显示图片）
            if len(images) == 0:
                # 检查内容中是否有跳转提示
                content_lower = content.lower()
                has_jump_hint = any(keyword in content_lower for keyword in ['查看图片', '查看视频', 'm.weibo.cn', 'weibo.com'])
                # 检查是否有跳转链接
                jump_links = weibo_block.xpath('.//a[contains(@href, "weibo.com") or contains(@href, "m.weibo.cn")]/@href')
                
                # 如果有跳转提示或链接，尝试补充获取
                if has_jump_hint or jump_links:
                    need_supplement = True
            
            # 情况3：如果图片为0，但内容中有相关关键词，尝试补充获取图片
            if len(images) == 0:
                content_lower = content.lower()
                # 检查是否有图片相关的关键词
                image_keywords = ['图片', 'photo', '图', '照']
                if any(keyword in content_lower for keyword in image_keywords):
                    need_supplement = True
            
            # 从 m.weibo.cn 补充获取图片信息（视频已在主流程中获取）
            if need_supplement:
                print('  检测到需要补充获取图片信息（从 m.weibo.cn）...')
                mobile_data = self._get_weibo_from_mobile(self.wid)
                if mobile_data:
                    # 合并图片（去重）
                    mobile_images = mobile_data.get('images', [])
                    for img in mobile_images:
                        if img not in images:
                            images.append(img)
                    
                    if mobile_images:
                        print(f'  补充获取: {len(mobile_images)} 张图片')
                    else:
                        print('  补充获取: 未找到图片')
                    
                    # 如果补充获取到图片且启用下载，下载这些图片
                    if self.download_images and mobile_images:
                        print('  开始下载补充获取的图片...')
                        start_idx = len(images) - len(mobile_images) + 1
                        for idx, img_url in enumerate(mobile_images, start_idx):
                            save_filename = f'{self.wid}_{idx}.jpg'
                            save_path = os.path.join(self.images_dir, save_filename)
                            self._download_image(img_url, save_path)
                            save_path = os.path.join(get_output_dir(), save_filename)
                            self._download_image(img_url, save_path)
            
            # 如果启用视频下载，下载视频
            if self.download_videos and videos:
                print('  开始下载视频...')
                for idx, video_url in enumerate(videos, 1):
                    # 确定文件扩展名
                    if '.mp4' in video_url.lower():
                        ext = '.mp4'
                    elif '.m3u8' in video_url.lower():
                        ext = '.m3u8'
                    elif '.flv' in video_url.lower():
                        ext = '.flv'
                    else:
                        ext = '.mp4'  # 默认使用mp4
                    
                    # 使用 get_output_dir() 作为保存目录，与 test_download_video.py 一致
                    save_filename = f'{self.wid}_{idx}{ext}'
                    output_path = os.path.join(get_output_dir(), save_filename)
                    self._download_video(video_url, output_path)
            
            # 组装数据
            self.weibo_data = {
                'wid': self.wid,
                'weibo_id': weibo_id,
                'user_id': user_id,
                'user_name': user_name[0] if user_name else '',
                'content': content,
                'images': images,
                'image_count': len(images),
                'videos': videos,
                'video_count': len(videos),
                'publish_time': publish_time,
                'publish_source': publish_source,
                'like_count': like_count,
                'repost_count': repost_count,
                'comment_count': comment_count,
                'weibo_url': f'https://weibo.cn/comment/{self.wid}',
            }
            
            print(f'✓ 微博内容提取完成')
            print(f'  作者: {self.weibo_data["user_name"]}')
            print(f'  内容: {content[:50]}...' if len(content) > 50 else f'  内容: {content}')
            print(f'  图片: {len(images)} 张')
            if videos:
                print(f'  视频: {len(videos)} 个')
            print(f'  点赞: {like_count} | 转发: {repost_count} | 评论: {comment_count}')
            
            return self.weibo_data
            
        except Exception as e:
            print(f'❌ 提取微博内容失败: {e}')
            traceback.print_exc()
            return None
    
    # ==================== 评论爬取 ====================
    
    def get_all_comments(self, max_pages=None):
        """
        获取所有评论（包括回复）
        
        Args:
            max_pages: 最大爬取页数（None表示全部爬取）
        
        Returns:
            list: 评论列表
        """
        print('\n[2/4] 正在爬取评论...')
        
        url = f'https://weibo.cn/comment/{self.wid}'
        first_page = self._parse_html(url)
        
        if first_page is None:
            print('❌ 无法访问评论页面')
            return []
        
        # 优先使用 get_weibo_content() 中已提取的评论数
        total_comments = 0
        if self.weibo_data and 'comment_count' in self.weibo_data:
            total_comments = self.weibo_data.get('comment_count', 0)
            if total_comments > 0:
                print(f'  使用已提取的评论总数: {total_comments}')
        
        # 如果未从weibo_data获取到，尝试从评论页面提取
        if total_comments == 0:
            comment_count_text = first_page.xpath('//span[@class="cmt"]/text()')
            if comment_count_text:
                match = re.search(r'评论\[(\d+)\]', comment_count_text[0])
                if match:
                    total_comments = int(match.group(1))
            else:
                # 备用方法：从页面文本中提取
                page_text = first_page.xpath('string(.)')
                match = re.search(r'评论\[(\d+)\]', page_text)
                if match:
                    total_comments = int(match.group(1))
        
        from math import ceil
        
        # 如果设置了max_pages，优先使用max_pages；否则根据total_comments计算
        if max_pages:
            # 如果设置了最大页数限制，直接使用该限制
            total_pages = max_pages
            if total_comments > 0:
                # 如果成功提取到评论总数，取两者中的较小值
                calculated_pages = ceil(total_comments / 10)
                total_pages = min(calculated_pages, max_pages)
        else:
            # 如果没有设置max_pages，根据total_comments计算
            if total_comments > 0:
                total_pages = ceil(total_comments / 10)
            else:
                # 如果无法获取评论总数，默认爬取1页（实际可能更多，但需要动态检测）
                total_pages = 1
        
        if total_comments > 0:
            print(f'  评论总数: {total_comments}')
        else:
            print(f'  评论总数: {total_comments}（无法获取，将尝试爬取）')
        
        if max_pages:
            print(f'  页数限制: {max_pages} 页')
        print(f'  需爬取页数: {total_pages}')
        
        comments = []
        
        for page in range(1, total_pages + 1):
            print(f'  正在爬取第 {page}/{total_pages} 页...', end=' ')
            
            page_url = f'https://weibo.cn/comment/{self.wid}?page={page}'
            selector = self._parse_html(page_url)
            
            if selector is None:
                print('失败')
                continue
            
            # 获取所有评论块 - 参考WeiboCommentScrapy.py：使用starts-with(@id,'C')更准确
            comment_blocks = selector.xpath("/html/body/div[starts-with(@id,'C')]")
            
            # 如果没有找到，尝试备用方法
            if not comment_blocks:
                comment_blocks = selector.xpath("//div[@class='c'][starts-with(@id,'C')]")
            
            page_comments = 0
            
            for block in comment_blocks:
                try:
                    comment_id_full = block.xpath('@id')[0]
                    if not comment_id_full.startswith('C_'):
                        continue
                    
                    # 跳过热门评论（包含<span class="kt">[热门]</span>标签）
                    hot_tag = block.xpath('.//span[@class="kt"]')
                    if hot_tag:
                        hot_text = ''.join(hot_tag[0].xpath('.//text()'))
                        if '热门' in hot_text:
                            continue  # 跳过热门评论
                    
                    comment_id = comment_id_full[2:]  # 移除'C_'前缀
                    
                    # 评论者信息 - 参考WeiboCommentScrapy.py：取第一个<a>标签
                    commenter_link_elements = block.xpath('.//a[1]/@href')
                    commenter_name_elements = block.xpath('.//a[1]/text()')
                    
                    commenter_id = None
                    commenter_name = ''
                    
                    if commenter_link_elements:
                        commenter_link = commenter_link_elements[0]
                        # 从链接中提取用户ID：/u/7995771776
                        match = re.search(r'/u/(\d+)', commenter_link)
                        if match:
                            commenter_id = match.group(1)
                    
                    if commenter_name_elements:
                        commenter_name = commenter_name_elements[0].strip()
                    
                    # 评论内容 - 参考WeiboCommentScrapy.py的逻辑
                    content = ''
                    content_span = block.xpath('.//span[@class="ctt"]')
                    
                    if content_span:
                        # 先尝试获取文本内容
                        content_text = content_span[0].xpath('text()')
                        if content_text and len(content_text) > 0:
                            content = content_text[0]
                            # 处理回复格式
                            if '回复' in content or len(content.strip()) == 0:
                                # 使用string(.)获取所有文本（包括子元素）
                                content = content_span[0].xpath('string(.)').strip()
                                # 移除"回复@xxx:"前缀
                                if '回复' in content:
                                    colon_idx = content.find(':')
                                    if colon_idx > 0:
                                        content = content[colon_idx + 1:].strip()
                        else:
                            # 如果text()为空，使用string(.)获取所有文本
                            content = content_span[0].xpath('string(.)').strip()
                    
                    # 如果仍然为空，尝试从整个block提取
                    if not content or len(content.strip()) == 0:
                        full_text = block.xpath('string(.)').strip()
                        if ':' in full_text:
                            content = full_text.split(':', 1)[1].strip()
                        else:
                            content = full_text
                    
                    content = self._clean_text(content)
                    
                    # 点赞数 - 参考WeiboCommentScrapy.py：从<span class="cc">[1]/a/text()提取
                    like_count = 0
                    like_spans = block.xpath('.//span[@class="cc"][1]/a/text()')
                    if like_spans:
                        like_text = like_spans[0]
                        # 提取格式：赞[0] -> 0
                        match = re.search(r'赞\[(\d+)\]', like_text)
                        if match:
                            like_count = int(match.group(1))
                    
                    # 备用方法：从attitude链接中提取
                    if like_count == 0:
                        like_links = block.xpath('.//a[contains(@href, "/attitude/")]/text()')
                        for text in like_links:
                            match = re.search(r'赞\[(\d+)\]', text)
                            if match:
                                like_count = int(match.group(1))
                                break
                    
                    # 发布时间和来源 - 参考WeiboCommentScrapy.py
                    time_spans = block.xpath('.//span[@class="ct"]/text()')
                    publish_time = ''
                    publish_source = ''
                    
                    if time_spans:
                        time_str = time_spans[0]
                        # 提取来源信息（在"来自"之后）
                        if '来自' in time_str:
                            time_part = time_str.split('来自')[0].strip()
                            publish_source = time_str.split('来自')[1].strip()
                        else:
                            time_part = time_str.strip()
                        
                        publish_time = self._parse_time(time_part)
                    
                    comment_data = {
                        'comment_id': comment_id,
                        'commenter_id': commenter_id,
                        'commenter_name': commenter_name,
                        'content': content,
                        'like_count': like_count,
                        'publish_time': publish_time,
                        'publish_source': publish_source,
                    }
                    
                    comments.append(comment_data)
                    page_comments += 1
                    
                except Exception as e:
                    print(f'\n  解析评论失败: {e}')
                    traceback.print_exc()
                    continue
            
            print(f'获取 {page_comments} 条评论')
            
            # 随机延时避免被限制
            if page < total_pages:
                time.sleep(random.uniform(1.5, 3))
        
        self.comments_data = comments
        print(f'✓ 评论爬取完成，共 {len(comments)} 条')
        
        return comments
    
    # ==================== 转发爬取 ====================
    
    def get_all_reposts(self, max_pages=None):
        """
        获取所有转发信息
        
        Args:
            max_pages: 最大爬取页数（None表示全部爬取）
        
        Returns:
            list: 转发列表
        """
        print('\n[3/4] 正在爬取转发...')
        
        url = f'https://weibo.cn/repost/{self.wid}'
        first_page = self._parse_html(url)
        
        if first_page is None:
            print('❌ 无法访问转发页面')
            return []
        
        # 优先从分页元素中提取总页数（最准确的方法）
        total_pages = 0
        pagelist_div = first_page.xpath('//div[@id="pagelist"]')
        if pagelist_div:
            pagelist_text = ''.join(pagelist_div[0].xpath('string(.)'))
            # 提取格式：15/121页 -> 121
            page_match = re.search(r'(\d+)/(\d+)页', pagelist_text)
            if page_match:
                total_pages = int(page_match.group(2))
                print(f'  从分页元素提取到总页数: {total_pages}')
        
        # 如果未从分页元素获取到，尝试从转发总数计算
        if total_pages == 0:
            total_reposts = 0
            if self.weibo_data and 'repost_count' in self.weibo_data:
                total_reposts = self.weibo_data.get('repost_count', 0)
                if total_reposts > 0:
                    print(f'  使用已提取的转发总数: {total_reposts}')
            
            # 如果未从weibo_data获取到，尝试从转发页面提取
            if total_reposts == 0:
                # 方法1：从转发页面的id="attitude"div中提取
                attitude_div = first_page.xpath('//div[@id="attitude"]')
                if attitude_div:
                    attitude_text = ''.join(attitude_div[0].xpath('string(.)'))
                    repost_match = re.search(r'转发\[(\d+)\]', attitude_text)
                    if repost_match:
                        total_reposts = int(repost_match.group(1))
                
                # 方法2：从页面文本中提取
                if total_reposts == 0:
                    page_text = first_page.xpath('string(.)')
                    repost_match = re.search(r'转发\[(\d+)\]', page_text)
                    if repost_match:
                        total_reposts = int(repost_match.group(1))
            
            from math import ceil
            
            # 根据转发总数计算页数
            if total_reposts > 0:
                calculated_pages = ceil(total_reposts / 10)
                total_pages = calculated_pages
                print(f'  根据转发总数计算页数: {total_pages} (转发总数: {total_reposts})')
            else:
                print(f'  转发总数: {total_reposts}（无法获取）')
        
        # 如果设置了max_pages，限制总页数
        if max_pages:
            original_total_pages = total_pages
            total_pages = min(total_pages, max_pages) if total_pages > 0 else max_pages
            print(f'  页数限制: {max_pages} 页')
            if original_total_pages > 0 and original_total_pages != total_pages:
                print(f'  实际总页数: {original_total_pages}，限制后: {total_pages}')
        
        if total_pages == 0:
            # 如果无法获取总页数，默认爬取1页（实际可能更多，但需要动态检测）
            total_pages = 1
            print(f'  无法获取总页数，默认爬取: {total_pages} 页')
        else:
            print(f'  需爬取页数: {total_pages}')
        
        reposts = []
        seen_reposts = set()  # 用于去重：存储(user_id, publish_time)元组
        
        for page in range(1, total_pages + 1):
            print(f'  正在爬取第 {page}/{total_pages} 页...', end=' ')
            
            page_url = f'https://weibo.cn/repost/{self.wid}?page={page}'
            selector = self._parse_html(page_url)
            
            if selector is None:
                print('失败')
                continue
            
            # 获取所有转发块（参考WeiboRepostSpider.py的逻辑）
            # 只选择包含span[@class='cc']和span[@class='ct']的块，这些才是真正的转发条目
            repost_blocks = selector.xpath("//div[@class='c']")
            page_reposts = 0
            has_content = False
            
            for block in repost_blocks:
                try:
                    # 检查是否包含必要的元素（参考WeiboRepostSpider.py）
                    user_link = block.xpath('./a[1]/@href')
                    user_name = block.xpath('./a[1]/text()')
                    cc_text = block.xpath(".//span[@class='cc']/a/text()")  # 点赞链接
                    ct_text = block.xpath(".//span[@class='ct']/text()")     # 时间文本
                    
                    # 过滤非转发块：必须包含用户链接、用户名、cc和ct
                    if not user_link or not user_name or not cc_text or not ct_text:
                        continue
                    
                    has_content = True
                    
                    # 提取用户ID（从链接末尾提取，如 /5695608993）
                    user_id = None
                    match = re.search(r'/(\d+)$', user_link[0])
                    if match:
                        user_id = match.group(1)
                    
                    # 提取点赞数（从span[@class='cc']中提取）
                    like_count = 0
                    like_match = re.search(r'赞\[(\d+)\]', cc_text[0])
                    if like_match:
                        like_count = int(like_match.group(1))
                    
                    # 提取发布时间
                    publish_time = ''
                    if ct_text:
                        publish_time = self._parse_time(ct_text[0])
                    
                    # 使用(user_id, publish_time)作为唯一标识去重
                    unique_key = (user_id, publish_time)
                    if unique_key in seen_reposts:
                        continue  # 跳过重复的转发
                    seen_reposts.add(unique_key)
                    
                    # 提取转发内容
                    full_text = ''.join(block.xpath('string(.)'))
                    
                    # 移除时间部分
                    if ct_text and ct_text[0] in full_text:
                        full_text = full_text[:full_text.rfind(ct_text[0])]
                    
                    # 移除点赞文本
                    full_text = re.sub(r'赞\[\d+\]', '', full_text)
                    
                    # 提取转发内容（移除用户名和其他杂项）
                    content = full_text
                    if user_name[0] + ':' in content:
                        content = content.split(user_name[0] + ':', 1)[1]
                    elif user_name[0] in content:
                        # 如果用户名后面没有冒号，尝试直接分割
                        parts = content.split(user_name[0], 1)
                        if len(parts) > 1:
                            content = parts[1]
                    content = self._clean_text(content)
                    
                    repost_data = {
                        'user_id': user_id,
                        'user_name': user_name[0],
                        'content': content,
                        'like_count': like_count,
                        'publish_time': publish_time,
                    }
                    
                    reposts.append(repost_data)
                    page_reposts += 1
                    
                except Exception as e:
                    continue
            
            # 如果当前页没有内容，检查是否还有下一页
            if not has_content:
                # 方法1：检查分页元素中的当前页/总页数
                pagelist_div = selector.xpath('//div[@id="pagelist"]')
                if pagelist_div:
                    pagelist_text = ''.join(pagelist_div[0].xpath('string(.)'))
                    page_match = re.search(r'(\d+)/(\d+)页', pagelist_text)
                    if page_match:
                        current_page_num = int(page_match.group(1))
                        total_page_num = int(page_match.group(2))
                        if current_page_num < total_page_num:
                            # 如果当前页小于总页数，说明还有更多页
                            print(f'当前页无内容，但分页显示 {current_page_num}/{total_page_num}，继续...')
                        else:
                            # 如果当前页等于总页数，说明已经到最后一页
                            print('无内容，已到最后一页，停止')
                            break
                    else:
                        # 方法2：检查是否有"下一页"链接
                        next_page_links = selector.xpath('//a[contains(text(), "下页") or contains(text(), "下一页")]/@href')
                        if next_page_links:
                            print('当前页无内容，但检测到下一页链接，继续...')
                        else:
                            print('无内容，停止')
                            break
                else:
                    # 方法3：检查是否有"下一页"链接（备用方法）
                    next_page_links = selector.xpath('//a[contains(text(), "下页") or contains(text(), "下一页")]/@href')
                    if next_page_links:
                        print('当前页无内容，但检测到下一页链接，继续...')
                    else:
                        print('无内容，停止')
                        break
            else:
                print(f'获取 {page_reposts} 条转发')
            
            # 随机延时
            if page < total_pages:
                time.sleep(random.uniform(1.5, 3))
        
        self.reposts_data = reposts
        print(f'✓ 转发爬取完成，共 {len(reposts)} 条')
        
        return reposts
    
    # ==================== 统计分析 ====================
    
    def generate_stats(self):
        """生成互动统计分析"""
        print('\n[4/4] 正在生成统计分析...')
        
        self.stats = {
            'weibo_info': {
                'wid': self.wid,
                'user_name': self.weibo_data.get('user_name', ''),
                'publish_time': self.weibo_data.get('publish_time', ''),
                'content_length': len(self.weibo_data.get('content', '')),
                'image_count': self.weibo_data.get('image_count', 0),
            },
            'interaction_stats': {
                'like_count': self.weibo_data.get('like_count', 0),
                'repost_count': len(self.reposts_data),
                'comment_count': len(self.comments_data),
                'total_interactions': self.weibo_data.get('like_count', 0) + len(self.reposts_data) + len(self.comments_data),
            },
            'comment_stats': {
                'total_comments': len(self.comments_data),
                'top_commenters': self._get_top_commenters(),
                'avg_comment_length': self._avg_length([c['content'] for c in self.comments_data]),
            },
            'repost_stats': {
                'total_reposts': len(self.reposts_data),
                'top_reposters': self._get_top_reposters(),
                'avg_repost_length': self._avg_length([r['content'] for r in self.reposts_data]),
            },
        }
        
        print('✓ 统计分析完成')
        print(f'  总互动数: {self.stats["interaction_stats"]["total_interactions"]}')
        print(f'  评论数: {len(self.comments_data)} | 转发数: {len(self.reposts_data)} | 点赞数: {self.weibo_data.get("like_count", 0)}')
        
        return self.stats
    
    def _get_top_commenters(self, top_n=10):
        """获取评论最多的用户"""
        from collections import Counter
        commenter_counts = Counter([c['commenter_name'] for c in self.comments_data])
        return [{'name': name, 'count': count} for name, count in commenter_counts.most_common(top_n)]
    
    def _get_top_reposters(self, top_n=10):
        """获取转发最多的用户"""
        from collections import Counter
        reposter_counts = Counter([r['user_name'] for r in self.reposts_data])
        return [{'name': name, 'count': count} for name, count in reposter_counts.most_common(top_n)]
    
    def _avg_length(self, texts):
        """计算平均长度"""
        if not texts:
            return 0
        return sum(len(t) for t in texts) / len(texts)
    
    # ==================== 数据导出 ====================
    
    def export_json(self):
        """导出完整JSON数据"""
        output_file = os.path.join(self.wid_dir, f'{self.wid}_complete.json')
        
        data = {
            'weibo_content': self.weibo_data,
            'comments': self.comments_data,
            'reposts': self.reposts_data,
            'stats': self.stats,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f'✓ JSON数据已导出: {output_file}')
        return output_file
    
    def export_csv(self):
        """导出CSV格式数据"""
        # 导出微博内容
        weibo_file = os.path.join(self.wid_dir, f'{self.wid}_weibo.csv')
        with open(weibo_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['微博ID', '作者', '内容', '图片数', '视频数', '视频链接', '发布时间', '来源', '点赞数', '转发数', '评论数', '链接'])
            # 视频链接用分号分隔
            video_links_str = '; '.join(self.weibo_data.get('videos', [])) if self.weibo_data.get('videos') else ''
            writer.writerow([
                self.weibo_data.get('wid', ''),
                self.weibo_data.get('user_name', ''),
                self.weibo_data.get('content', ''),
                self.weibo_data.get('image_count', 0),
                self.weibo_data.get('video_count', 0),
                video_links_str,
                self.weibo_data.get('publish_time', ''),
                self.weibo_data.get('publish_source', ''),
                self.weibo_data.get('like_count', 0),
                self.weibo_data.get('repost_count', 0),
                self.weibo_data.get('comment_count', 0),
                self.weibo_data.get('weibo_url', ''),
            ])
        
        # 导出评论
        comments_file = os.path.join(self.wid_dir, f'{self.wid}_comments.csv')
        with open(comments_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['评论ID', '评论者ID', '评论者昵称', '评论内容', '点赞数', '发布时间', '来源'])
            for c in self.comments_data:
                writer.writerow([
                    c.get('comment_id', ''),
                    c.get('commenter_id', ''),
                    c.get('commenter_name', ''),
                    c.get('content', ''),
                    c.get('like_count', 0),
                    c.get('publish_time', ''),
                    c.get('publish_source', ''),
                ])
        
        # 导出转发
        reposts_file = os.path.join(self.wid_dir, f'{self.wid}_reposts.csv')
        with open(reposts_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['转发者ID', '转发者昵称', '转发内容', '点赞数', '发布时间'])
            for r in self.reposts_data:
                writer.writerow([
                    r.get('user_id', ''),
                    r.get('user_name', ''),
                    r.get('content', ''),
                    r.get('like_count', 0),
                    r.get('publish_time', ''),
                ])
        
        # 导出统计数据
        stats_file = os.path.join(self.wid_dir, f'{self.wid}_stats.csv')
        with open(stats_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['统计项', '数值'])
            writer.writerow(['总点赞数', self.stats['interaction_stats']['like_count']])
            writer.writerow(['总转发数', self.stats['interaction_stats']['repost_count']])
            writer.writerow(['总评论数', self.stats['interaction_stats']['comment_count']])
            writer.writerow(['总互动数', self.stats['interaction_stats']['total_interactions']])
            writer.writerow(['平均评论长度', f"{self.stats['comment_stats']['avg_comment_length']:.1f}"])
            writer.writerow(['平均转发长度', f"{self.stats['repost_stats']['avg_repost_length']:.1f}"])
        
        print(f'✓ CSV数据已导出:')
        print(f'  - {weibo_file}')
        print(f'  - {comments_file}')
        print(f'  - {reposts_file}')
        print(f'  - {stats_file}')
        
        return weibo_file, comments_file, reposts_file, stats_file
    
    # ==================== 主流程 ====================
    
    def analyze(self, max_comment_pages=None, max_repost_pages=None):
        """
        执行完整的深度分析流程
        
        Args:
            max_comment_pages: 评论最大爬取页数（可选，如果未提供则从环境变量或.env文件读取）
            max_repost_pages: 转发最大爬取页数（可选，如果未提供则从环境变量或.env文件读取）
        """
        # 如果未提供参数，从环境变量读取
        if max_comment_pages is None:
            max_comment_pages = _read_int_env_value('MAX_COMMENT_PAGES', default=None)
        
        if max_repost_pages is None:
            max_repost_pages = _read_int_env_value('MAX_REPOST_PAGES', default=None)
        
        print('\n' + '=' * 80)
        print(f'开始深度分析微博: {self.wid}')
        if max_comment_pages:
            print(f'评论爬取限制: {max_comment_pages} 页（从 .env 文件读取）')
        else:
            print(f'评论爬取限制: 无限制（爬取全部）')
        if max_repost_pages:
            print(f'转发爬取限制: {max_repost_pages} 页（从 .env 文件读取）')
        else:
            print(f'转发爬取限制: 无限制（爬取全部）')
        print('=' * 80)
        
        start_time = time.time()
        
        # 0. 截图微博界面
        self.get_weibo_screenshot()

        # 1. 提取微博内容
        if not self.get_weibo_content():
            print('\n❌ 分析失败：无法获取微博内容')
            return False
        
        # 2. 爬取评论
        self.get_all_comments(max_pages=max_comment_pages)
        
        # 3. 爬取转发
        self.get_all_reposts(max_pages=max_repost_pages)
        
        # 4. 生成统计
        self.generate_stats()
        
        # 5. 导出数据
        print('\n' + '=' * 80)
        print('正在导出数据...')
        print('=' * 80)
        self.export_json()
        self.export_csv()
        
        elapsed_time = time.time() - start_time
        
        print('\n' + '=' * 80)
        print(f'✓ 深度分析完成！')
        print(f'  耗时: {elapsed_time:.1f} 秒')
        print(f'  输出目录: {self.wid_dir}')
        print('=' * 80 + '\n')
        
        return True


# ==================== 命令行使用示例 ====================

if __name__ == '__main__':
    """
    使用示例：
    
    1. 基本用法（爬取所有数据）：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z')
       analyzer.analyze()
    
    2. 从.env文件读取所有配置（推荐）：
       # 在.env文件中设置：
       # WID=QbelLys5Z
       # COOKIE=your_cookie_here
       # DOWNLOAD_IMAGES=false
       # MAX_COMMENT_PAGES=10
       # MAX_REPOST_PAGES=10
       # OUTPUT_DIR=weibo_analysis
       analyzer = WeiboDeepAnalyzer()  # 所有参数从.env读取
       analyzer.analyze()  # 页数限制也从.env读取
    
    3. 限制爬取页数（避免耗时过长）：
       # 方式1：在.env文件中设置 MAX_COMMENT_PAGES=10 和 MAX_REPOST_PAGES=10
       analyzer = WeiboDeepAnalyzer()
       analyzer.analyze()  # 自动从.env读取页数限制
       
       # 方式2：手动指定页数（会覆盖.env中的设置）
       analyzer = WeiboDeepAnalyzer()
       analyzer.analyze(max_comment_pages=10, max_repost_pages=10)
    
    4. 启用图片下载：
       # 方式1：在.env文件中设置 DOWNLOAD_IMAGES=true
       analyzer = WeiboDeepAnalyzer()  # download_images从.env读取
       analyzer.analyze()
       
       # 方式2：手动指定（会覆盖.env中的设置）
       analyzer = WeiboDeepAnalyzer(download_images=True)
       analyzer.analyze()
    
    5. 自定义Cookie：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z', cookie='your_cookie_here')
       analyzer.analyze()
    
    6. 只获取特定数据：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z')
       analyzer.get_weibo_content()
       analyzer.get_all_comments(max_pages=5)
       analyzer.export_json()
    """
    
    # 分析单条微博
    # 如果.env文件中设置了相关参数，可以直接调用而不传参数
    try:
        # 方式1：从.env文件读取所有配置（推荐，更安全）
        # 在.env文件中设置：
        # WID=QbelLys5Z
        # COOKIE=your_cookie_here
        # DOWNLOAD_IMAGES=false
        # MAX_COMMENT_PAGES=10
        # MAX_REPOST_PAGES=10
        # OUTPUT_DIR=weibo_analysis
        analyzer = WeiboDeepAnalyzer()  # 所有参数从.env文件读取
        
        # 方式2：部分参数从.env读取，部分手动指定
        # analyzer = WeiboDeepAnalyzer(download_images=True)  # wid和cookie从.env读取，download_images手动指定
        
        analyzer.analyze()  # max_comment_pages和max_repost_pages从.env读取
        
    except Exception as e:
        print(f'\n❌ 程序执行失败: {e}')
        traceback.print_exc()

