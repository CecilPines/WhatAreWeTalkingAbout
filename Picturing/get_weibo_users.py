import random
import time
from Picturing.spider import Spider
import requests
import json

def get_weibo_users(weibo_uid_list):
    if len(weibo_uid_list) >= 40:
        weibo_uid_list = random.sample(weibo_uid_list, 40)
    weibo_users = []
    for uid in weibo_uid_list:
        # time.sleep(random.uniform(1, 1.5))  # 随机等待1-3秒
        spider = Spider(int(uid), 0)
        weibo_data = spider.get_info(int(uid))
        weibo_users.append(weibo_data)
    return weibo_users
