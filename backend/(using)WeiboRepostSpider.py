# -*- coding: utf-8 -*-
# author:           generated based on project style
# create_time:      2025/10/28
# description:      Crawl repost timeline of a single weibo (cn site)

import requests
from lxml import etree
import os
import csv
import re
import time
import random

requests.packages.urllib3.disable_warnings()

def _read_cookie_from_env_file():
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


class WeiboRepostSpider(object):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    slp_sec_per_req = 2
    timeout = 10

    def __init__(self, wid, cookie=None):
        self.wid = wid
        self.cookie = cookie if cookie else _read_cookie_from_env_file()
        if not self.cookie:
            raise Exception('COOKIE 为空，请配置环境变量或无 GUI 功能独立版/.env 中的 COOKIE')
        self.headers['Cookie'] = self.cookie

        # 使用 Session，并关闭环境代理，避免走 127.0.0.1 等系统代理
        self.ss = requests.Session()
        self.ss.trust_env = False
        self.ss.headers.update(self.headers)

        # 输出到脚本同级目录下的 repost 文件夹，避免工作目录不同导致找不到
        self.repost_folder = os.path.join(os.path.dirname(__file__), 'repost')
        if not os.path.exists(self.repost_folder):
            os.mkdir(self.repost_folder)
        self.result_file = os.path.join(self.repost_folder, f'{self.wid}.csv')

        self.got = []
        self.got_num = 0
        self.written_num = 0

    def parse_one_page(self, html):
        # 参考 WeiboUserScrapy.py，统一使用 bytes 以避免含编码声明的 Unicode 触发解析异常
        selector = etree.HTML(html.encode('utf-8'))
        if selector is None:
            print('debug: etree selector is None')
            return []
        # 单页结构: /html/body/div[@class='c'] 多个，其中部分为工具条/翻页，需过滤
        blocks = selector.xpath("/html/body/div[@class='c']")
        print(f'debug: found blocks = {len(blocks)}')
        results = []
        for b in blocks:
            # 需要包含 span[@class='cc'] 和 span[@class='ct'] 的才是转发条目
            uid_link = b.xpath("./a[1]/@href")
            name_text = b.xpath("./a[1]/text()")
            cc_text = b.xpath(".//span[@class='cc']/a/text()")
            ct_text = b.xpath(".//span[@class='ct']/text()")
            # 内容文本，粗略做法：块完整文本去掉尾部时间来源
            full_text = ''.join(b.xpath('string(.)'))
            # 过滤非转发块
            if not uid_link or not name_text or not cc_text or not ct_text:
                continue

            # 1) 转发者 uid
            # 形如 /5695608993 -> 取数字
            uid = None
            try:
                m = re.search(r"/(\d+)$", uid_link[0])
                if m:
                    uid = m.group(1)
            except Exception:
                uid = None

            # 2) 点赞数量：来自 赞[0]
            like_count = 0
            try:
                m = re.search(r"赞\[(\d+)\]", cc_text[0])
                if m:
                    like_count = int(m.group(1))
            except Exception:
                like_count = 0

            # 3) 文本内容：按照“昵称:内容\xa0”抽取，或基于 HTML 去标签后的字符串裁剪
            content = ''
            try:
                # 构造昵称前缀: "{name}:"
                name = name_text[0]
                # full_text 示例："鬼疡:转发文本在此 赞[0]  41分钟前 来自微博手机版"
                # 先去掉尾部时间来源片段（span.ct 的文本）
                ct = ct_text[0]
                head = full_text
                if ct and ct in head:
                    head = head[:head.rfind(ct)]
                # 去掉点赞片段
                head = re.sub(r"赞\[\d+\]", "", head)
                # 定位 昵称:
                idx = head.find(name + ':')
                if idx >= 0:
                    content = head[idx + len(name) + 1:].strip()
                else:
                    # 回退：去掉昵称与前缀后，截取到第一个连续空白前
                    # 直接尝试用 span.cc 前的文本
                    raw_before_cc = ''.join(b.xpath("string(./text())")).strip()
                    if raw_before_cc:
                        content = raw_before_cc
                # 清理不可见空白
                content = re.sub(r"\s+", " ", content).strip()
            except Exception:
                content = ''

            # 4) 时间来源（可选）
            created = ct_text[0].strip() if ct_text else ''

            if uid:
                results.append({
                    'uid': uid,
                    'content': content,
                    'like_count': like_count,
                    'created': created
                })
        print(f'debug: parsed repost items = {len(results)}')
        return results

    def write_csv(self):
        result_headers = ['uid', 'content', 'like_count', 'created']
        result_data = [w.values() for w in self.got][self.written_num:]
        with open(self.result_file, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if self.written_num == 0 and not os.path.exists(self.result_file):
                writer.writerows([result_headers])
            elif self.written_num == 0 and os.path.getsize(self.result_file) == 0:
                writer.writerows([result_headers])
            writer.writerows(result_data)
        self.written_num = self.got_num
        print(f'debug: wrote rows, total_written={self.written_num}')

    def run(self, max_pages=100000):
        page = 1
        wrote_every = 5
        while page <= max_pages:
            url = f'https://weibo.cn/repost/{self.wid}?page={page}'
            try:
                print(f'debug: GET {url}')
                res = self.ss.get(url, timeout=self.timeout, verify=False)
            except Exception:
                print('debug: request exception, break')
                break
            if res.status_code != 200 or not res.text:
                print(f'debug: bad status or empty body, status={res.status_code}, body_len={len(res.text) if res.text else 0}')
                break
            print(f'debug: status={res.status_code}, body_len={len(res.text)}')
            print(f'debug: body_snippet={res.text[:200]}')

            page_items = self.parse_one_page(res.text)
            if not page_items:
                # 连续空页或无有效块，认为结束
                print('debug: no items parsed on this page, stop')
                break

            for it in page_items:
                self.got.append(it)
                self.got_num += 1

            if page % wrote_every == 0 and self.got_num > self.written_num:
                self.write_csv()

            page += 1
            time.sleep(random.randint(self.slp_sec_per_req, self.slp_sec_per_req + 2))

        if self.got_num > self.written_num:
            self.write_csv()
        print(f'debug: finished. total_got={self.got_num}, output={os.path.abspath(self.result_file)}')


if __name__ == '__main__':
    # 示例：从环境变量或 .env 读取 COOKIE，抓取指定 wid 的全部转发
    WeiboRepostSpider(wid='QbelLys5Z').run()


