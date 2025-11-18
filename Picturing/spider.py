
import time
import random
import os
import re
import json
from bs4 import BeautifulSoup
from Picturing.ProxyPool import Proxy_pool
from GetOutput import get_project_root
# 获取项目根路径
dir = os.getcwd()

proxy_pool = Proxy_pool()


# 工具类
class util(object):
    # 获取代理池
    @staticmethod
    def get_user_agent():
        MY_USER_AGENT = []
        user_agent_path = os.path.join(get_project_root(), "Picturing", "user_agent.txt")
        with open(user_agent_path, encoding="utf-8", mode="r") as f:
            for line in f:
                # print(line.strip('\n'))
                MY_USER_AGENT.append(line.strip('\n'))
        return MY_USER_AGENT

    '''这里区分新旧cookie池的依据是二者的UI设计新旧，weibo.cn看起来就很古老的那种ui，所以这里就称其为旧cookie池了'''

    # 获取weibo.com的cookie池（新cookie池）
    @staticmethod
    def get_new_cookies():
        MY_COOKIES = []
        new_cookies_path = os.path.join(get_project_root(), "Picturing", "new_cookies.txt")
        with open(new_cookies_path, encoding="utf-8", mode="r") as f:
            for line in f:
                # print(line.strip('\n'))
                MY_COOKIES.append(line.strip('\n'))
        return MY_COOKIES

    # 获取weibo.cn的cookie池（旧cookie池）
    @staticmethod
    def get_old_cookies():
        MY_COOKIES = []
        old_cookies_path = os.path.join(get_project_root(), "Picturing", "old_cookies.txt")
        with open(old_cookies_path, encoding="utf-8", mode="r") as f:
            for line in f:
                # print(line.strip('\n'))
                MY_COOKIES.append(line.strip('\n'))
        return MY_COOKIES

    # 随机从旧cookie池中选择一个cookie
    @staticmethod
    def get_cookie():
        cookie = {
            'cookie': random.choice(util.get_old_cookies())
        }
        return cookie

    # 随机从新cookie池中选择一个cookie
    @staticmethod
    def get_cookie1():
        cookie1 = {
            'cookie': random.choice(util.get_new_cookies())
        }
        return cookie1

    # 获取请求头
    @staticmethod
    def get_header():
        headers = {
            'User-Agent': random.choice(util.get_user_agent()),
            # 'DOWNLOAD_DELAY': 3,  ## 下载延时
        }
        return headers

    # 字符串转数字
    @staticmethod
    def to_num(string):
        pre = re.compile('\d')
        # for i in content_list:
        text = ''.join(pre.findall(string))
        # print(string)3
        if text == "":
            return 0
        else:
            return int(text)

    # 判断输入的三个数最小的
    @staticmethod
    def min(num1, num2, num3):
        min = num1
        if min > num2:
            min = num2
        if min > num3:
            min = num3
        return min


# 爬虫类
class Spider:
    user_url = ""
    fans_page_url_list = []

    # 对用户地址，以及粉丝数量初始化
    def __init__(self, user_id, num):
        self.user_url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{user_id}&since_id=".format(
            user_id=user_id)
        self.fans_page_url_list = [self.user_url + f"{begin}" for begin in range(num) if begin % 20 == 0]


    def get_info(self, id):
        user_home_page_url = "https://weibo.cn/u/{id}".format(id=id)
        # time.sleep(4)
        response = proxy_pool.get(url=user_home_page_url, headers=util.get_header(), cookies=util.get_cookie())
        html_content = response.text
        soup = BeautifulSoup(html_content, "lxml")

        data = {}

        # ---------- 基本信息区域 ----------
        # 用户头像
        avatar = soup.select_one("img.por")
        data["avatar"] = avatar["src"] if avatar else ""

        # 用户昵称与性别地区行
        user_info_span = soup.select_one("span.ctt")
        if user_info_span:
            text = user_info_span.get_text(" ", strip=True)
            # 昵称（去掉后面性别/地区等信息）
            data["nickname"] = text.split()[0] if text else ""
        else:
            data["nickname"] = ""

        # 性别 / 省份
        gender_area_match = re.search(r"(男|女)/(.*?)(\s|$)", html_content)
        if gender_area_match:
            data["gender"] = gender_area_match.group(1)
            data["location"] = gender_area_match.group(2).strip()
        else:
            data["gender"] = ""
            data["location"] = ""

        # 用户简介
        intro = None
        intro_spans = soup.select("span.ctt")
        if len(intro_spans) >= 2:
            intro = intro_spans[1].get_text(" ", strip=True)
        data["intro"] = intro or ""

        # ---------- 粉丝、关注、微博数 ----------
        stats = soup.select_one("div.tip2")
        data["stats"] = {}
        if stats:
            text = stats.get_text(" ", strip=True)

            wb = re.search(r"微博\[(\d+)\]", text)
            gz = re.search(r"关注\[(\d+)\]", text)
            fs = re.search(r"粉丝\[(\d+)\]", text)

            data["stats"]["weibo"] = int(wb.group(1)) if wb else 0
            data["stats"]["follow"] = int(gz.group(1)) if gz else 0
            data["stats"]["fans"] = int(fs.group(1)) if fs else 0

        # ---------- 微博列表 ----------
        weibo_items = []
        weibo_divs = soup.select("div.c[id^=M_]")

        for div in weibo_divs:
            item = {}

            # 微博正文
            content_span = div.select_one("span.ctt")
            item["content"] = content_span.get_text(" ", strip=True) if content_span else ""

            # 时间
            time_span = div.select_one("span.ct")
            item["time"] = time_span.get_text(strip=True) if time_span else ""

            # 点赞 / 评论 / 转发数
            html_text = div.get_text(" ", strip=True)
            zan = re.search(r"赞\[(\d+)\]", html_text)
            ping = re.search(r"评论\[(\d+)\]", html_text)
            zhuan = re.search(r"转发\[(\d+)\]", html_text)

            item["likes"] = int(zan.group(1)) if zan else 0
            item["comments"] = int(ping.group(1)) if ping else 0
            item["reposts"] = int(zhuan.group(1)) if zhuan else 0

            # 如果有图片
            pic = div.select_one("img")
            item["pic"] = pic["src"] if pic else ""

            weibo_items.append(item)

        data["weibo_list"] = weibo_items

        return json.dumps(data, ensure_ascii=False, indent=4)








def test():

    print("~" * 50 + "该爬虫仅用于交流学习，如果需要大量快速爬取请自行加入减少time.sleep时间" + "~" * 50)
    print("~" * 31 + "如果想要爬取多个人的信息，只需在目录中的id.txt填入id列表（一行一个）然后选择第三个模式即可开始爬取" + "~" * 31)
    a = input("请输入1或2或3选择要进行步骤：\n1.爬取输入用户信息\n2.爬取粉丝id\n3.爬取粉丝（多人）信息\n")
    if a == "1":
        user_id = input("请输入用户的id：")
        spider = Spider(int(user_id), 0)
        tmp = spider.get_info(int(user_id))
        print(tmp)
    elif a == "2":
        user_id = input("请输入用户的id：")
        fans_num = input("请输入想要获取的粉丝信息的数量：")
        spider = Spider(int(user_id), int(fans_num))
        spider.get_fans_id()
    # elif a == "3":
    #     spider = Spider(0, 0)
    #     id_list = []
    #     try:
    #         with open(dir + "\\id.txt", encoding="utf-8", mode="r") as f:
    #             for line in f:
    #                 id_list.append(line.strip('\n'))
    #         f.close()
    #         pool = ThreadPool(20)
    #         for i in range(0, len(id_list)):
    #             pool.run(func=spider.get_info, args=(id_list[i],))
    #         pool.close()
    #     except:
    #         print("未找到id.txt文件，请先提供id列表，或选择2模式获取id列表")
    # else:
    #     print("请输入1或2或3")

if __name__ == '__main__':
    test()
    pass