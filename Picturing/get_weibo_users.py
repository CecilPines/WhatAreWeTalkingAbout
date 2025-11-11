import random
import time

import requests
import json


def crawl_weibo_mobile(uid):
    """通过移动端API爬取微博数据:cite[4]"""
    # 获取容器ID
    url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': f'https://m.weibo.cn/u/{uid}',
        'Cookie': 'SCF=AtyUTbyVNTX2LKHPJAHM03grJ9z5Ry9JUAZ4D5RzNVDBbF6sQjA8LZE8F6PxKeITNupd7KyvFALsFjvpH-mGuEM.; XSRF-TOKEN=t-DnfJR193d146T0cyRDExmG; SUB=_2A25EDYbmDeRhGeNG7FIS8CjPwzmIHXVnYoYurDV8PUNbmtAYLWbDkW9NSzmsnVYwuUgthlxuAKMETtL7grPohqkk; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFdj8useJEFYkxELL8bZBT55NHD95Qf1hM7e05ce0nfWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNSKnNehe7SoeRSBtt; ALF=02_1764852662; WBPSESS=Dt2hbAUaXfkVprjyrAZT_F8d4eDY6jDajtOeyA_3nwv370Pd7MEud9N1aInuFG0jzb9O8FX-4vkntBYSUmTl5Hiu5VRSTO4gWjLttBjLPJ_I3RWir42BKG0QMDX93t2tJMyR-IWvWhEXH8yM6MMQKy6r-m9FENUqmGxhsCNzg_ePXVniO5IpoI_eTAm9Wv9O80Xv7tUWo_3OCp7vURUZWg=='
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        # 在 crawl_weibo_mobile 函数的 response = requests.get 后添加
        # print("响应状态码:", response.status_code)
        # print("响应内容:", response.text)
        #解决：在https://m.weibo.cn/重新登录并在该页面按F12获取cookie

        # 获取微博容器ID
        tabs = data['data']['tabsInfo']['tabs']
        weibo_containerid = None
        for tab in tabs:
            if tab.get('tab_type') == 'weibo':
                weibo_containerid = tab['containerid']
                break


        if weibo_containerid:
            # 获取微博列表
            weibo_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid={weibo_containerid}"
            weibo_response = requests.get(weibo_url, headers=headers)
            weibo_data = weibo_response.json()

            return {
                'user_info': data['data']['userInfo'],
                'weibo_list': weibo_data['data']['cards']
            }


    except Exception as e:
        print(f"爬取失败: {e}")

    return None


# def save_to_file(data, filename):
#     """将数据保存到JSON文件"""
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)


def get_weibo_users(weibo_uid_list):
    weibo_users = []
    for uid in weibo_uid_list:
        time.sleep(random.uniform(1, 3))  # 随机等待1-3秒
        weibo_data = crawl_weibo_mobile(uid)
        weibo_users.append(weibo_data)
    return weibo_users

