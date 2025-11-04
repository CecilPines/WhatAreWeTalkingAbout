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

import requests
from lxml import etree

requests.packages.urllib3.disable_warnings()


def _read_cookie_from_env_file():
    """从环境变量或.env文件读取Cookie"""
    env_cookie = os.environ.get('COOKIE')
    if env_cookie:
        return env_cookie
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'COOKIE':
                        return value.strip().strip('"').strip("'")
    except Exception:
        pass
    return ''


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
    
    def __init__(self, wid, cookie=None, output_dir='weibo_analysis', download_images=False):
        """
        初始化分析器
        
        Args:
            wid: 微博ID（可以是数字ID或mid）
            cookie: 微博Cookie（可选，从环境变量读取）
            output_dir: 输出目录
            download_images: 是否下载图片到本地（默认False）
        """
        self.wid = wid
        self.cookie = cookie if cookie else _read_cookie_from_env_file()
        self.download_images = download_images
        
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
            response = self._request(img_url, timeout=20)
            if response:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print('✓')
                time.sleep(0.5)
                return True
            else:
                print('✗ 下载失败')
                return False
        except Exception as e:
            print(f'✗ 下载失败: {e}')
            return False
    
    # ==================== 微博内容提取 ====================
    
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
            
            # 提取图片链接
            images = []
            pic_links = weibo_block.xpath('.//a[contains(@href, "/mblog/picAll/")]/@href')
            if pic_links:
                print('  检测到图片，正在提取...')
                pic_url = 'https://weibo.cn' + pic_links[0]
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
                
                time.sleep(1)
            
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
            # 使用更精确的xpath选择器
            like_count = 0
            repost_count = 0
            comment_count = 0
            
            # 方法1：从链接文本中提取
            like_links = weibo_block.xpath('.//a[contains(@href, "/attitude/")]//text()')
            for text in like_links:
                match = re.search(r'赞\[(\d+)\]', text)
                if match:
                    like_count = int(match.group(1))
                    break
            
            repost_links = weibo_block.xpath('.//a[contains(@href, "/repost/")]//text()')
            for text in repost_links:
                match = re.search(r'转发\[(\d+)\]', text)
                if match:
                    repost_count = int(match.group(1))
                    break
            
            # 评论数可能在<span class="pms">中
            comment_spans = weibo_block.xpath('.//span[@class="pms"]//text()')
            for text in comment_spans:
                match = re.search(r'评论\[(\d+)\]', text)
                if match:
                    comment_count = int(match.group(1))
                    break
            
            # 方法2：如果上述方法失败，使用footer_text作为备用
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
            
            # 组装数据
            self.weibo_data = {
                'wid': self.wid,
                'weibo_id': weibo_id,
                'user_id': user_id,
                'user_name': user_name[0] if user_name else '',
                'content': content,
                'images': images,
                'image_count': len(images),
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
        
        # 获取评论总数和页数 - 参考WeiboCommentScrapy.py的逻辑
        comment_count_text = first_page.xpath('//span[@class="cmt"]/text()')
        total_comments = 0
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
        total_pages = ceil(total_comments / 10) if total_comments > 0 else 1
        
        if max_pages:
            total_pages = min(total_pages, max_pages)
        
        print(f'  评论总数: {total_comments}')
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
        
        reposts = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
            
            print(f'  正在爬取第 {page} 页...', end=' ')
            
            page_url = f'https://weibo.cn/repost/{self.wid}?page={page}'
            selector = self._parse_html(page_url)
            
            if selector is None:
                print('失败')
                break
            
            # 获取所有转发块
            repost_blocks = selector.xpath("//div[@class='c']")
            page_reposts = 0
            has_content = False
            
            for block in repost_blocks:
                try:
                    # 需要包含用户链接和转发内容
                    user_link = block.xpath('./a[1]/@href')
                    user_name = block.xpath('./a[1]/text()')
                    
                    if not user_link or not user_name:
                        continue
                    
                    has_content = True
                    
                    # 提取用户ID
                    user_id = None
                    match = re.search(r'/(\d+)', user_link[0])
                    if match:
                        user_id = match.group(1)
                    
                    # 提取转发内容
                    full_text = ''.join(block.xpath('string(.)'))
                    
                    # 提取时间和来源
                    time_text = block.xpath('.//span[@class="ct"]/text()')
                    publish_time = ''
                    if time_text:
                        publish_time = self._parse_time(time_text[0])
                        # 从完整文本中移除时间部分
                        if publish_time in full_text:
                            full_text = full_text[:full_text.rfind(publish_time)]
                    
                    # 提取点赞数
                    like_count = 0
                    like_match = re.search(r'赞\[(\d+)\]', full_text)
                    if like_match:
                        like_count = int(like_match.group(1))
                        # 移除点赞文本
                        full_text = re.sub(r'赞\[\d+\]', '', full_text)
                    
                    # 提取转发内容（移除用户名和其他杂项）
                    content = full_text
                    if user_name[0] + ':' in content:
                        content = content.split(user_name[0] + ':', 1)[1]
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
            
            if not has_content:
                print('无内容，停止')
                break
            
            print(f'获取 {page_reposts} 条转发')
            
            page += 1
            
            # 随机延时
            if has_content:
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
            writer.writerow(['微博ID', '作者', '内容', '图片数', '发布时间', '来源', '点赞数', '转发数', '评论数', '链接'])
            writer.writerow([
                self.weibo_data.get('wid', ''),
                self.weibo_data.get('user_name', ''),
                self.weibo_data.get('content', ''),
                self.weibo_data.get('image_count', 0),
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
            max_comment_pages: 评论最大爬取页数
            max_repost_pages: 转发最大爬取页数
        """
        print('\n' + '=' * 80)
        print(f'开始深度分析微博: {self.wid}')
        print('=' * 80)
        
        start_time = time.time()
        
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
    
    2. 限制爬取页数（避免耗时过长）：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z')
       analyzer.analyze(max_comment_pages=10, max_repost_pages=10)
    
    3. 启用图片下载：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z', download_images=True)
       analyzer.analyze(max_comment_pages=10, max_repost_pages=10)
    
    4. 自定义Cookie：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z', cookie='your_cookie_here')
       analyzer.analyze()
    
    5. 只获取特定数据：
       analyzer = WeiboDeepAnalyzer(wid='QbelLys5Z')
       analyzer.get_weibo_content()
       analyzer.get_all_comments(max_pages=5)
       analyzer.export_json()
    """
    
    # 示例：分析单条微博（限制各10页）
    try:
        wid = 'QbelLys5Z'  # 替换为你要分析的微博ID
        
        analyzer = WeiboDeepAnalyzer(wid=wid, download_images=False)
        analyzer.analyze(max_comment_pages=10, max_repost_pages=10)
        
    except Exception as e:
        print(f'\n❌ 程序执行失败: {e}')
        traceback.print_exc()

