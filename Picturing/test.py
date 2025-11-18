import random
import time
import random
import requests
import json


def crawl_weibo_mobile(uid, cookie):
    """通过移动端API爬取微博数据:cite[4]"""
    # 获取容器ID
    url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}"
    # 常见浏览器User-Agent列表,轮换，避免被识别为爬虫
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"
    ]
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': f'https://m.weibo.cn/u/{uid}',
        'Cookie': 'SCF=AtyUTbyVNTX2LKHPJAHM03grJ9z5Ry9JUAZ4D5RzNVDBbF6sQjA8LZE8F6PxKeITNupd7KyvFALsFjvpH-mGuEM.; SINAGLOBAL=4076528723259.1465.1763358572863; ULV=1763358572865:1:1:1:4076528723259.1465.1763358572863:; XSRF-TOKEN=gKTKYBQQsmU9f-4eFj4pSTNv; PC_TOKEN=f18caf846b; SUB=_2A25EH2HkDeRhGeNG7FIS8CjPwzmIHXVnVfssrDV8PUNbmtB-LRnYkW9NSzmsnXnV9VZgHPbhf7MzCcLcmv8QwO3N; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFdj8useJEFYkxELL8bZBT55NHD95Qf1hM7e05ce0nfWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNSKnNehe7SoeRSBtt; ALF=02_1765973684; WBPSESS=Dt2hbAUaXfkVprjyrAZT_F8d4eDY6jDajtOeyA_3nwv370Pd7MEud9N1aInuFG0jzb9O8FX-4vkntBYSUmTl5Hiu5VRSTO4gWjLttBjLPJ_I3RWir42BKG0QMDX93t2tVJfEwMCzHZ-faBF3BnebXUV-QfrYFnTII-X3doAieNlDnQA203YQH86mL32I5qgKZDV3uFtVrx_VyXK_QRavEA=='

    }


    try:

        # 后续爬取使用同一个session
        response = requests.get(url, headers=headers)
        data = response.json()

        # 在 crawl_weibo_mobile 函数的 response = requests.get 后添加
        print("响应状态码:", response.status_code)
        print("响应内容:", response.text)
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


def get_weibo_users(weibo_uid_list, cookie):
    weibo_users = []
    for uid in weibo_uid_list:
        # time.sleep(random.uniform(1, 3))  # 随机等待1-3秒
        weibo_data = crawl_weibo_mobile(uid, cookie)
        weibo_users.append(weibo_data)
    return weibo_users


def batch_get_weibo_users(uid_list, cookie, batch_size=5, delay=2):
    """
    分批获取用户信息，减少单次请求压力

    :param uid_list: 用户ID列表
    :param batch_size: 每批处理的用户数量
    :param delay: 批次之间的延迟时间(秒)
    :return: 所有用户信息列表
    """
    if len(uid_list) >= 10:
        uid_list = random.sample(uid_list, 10)
    all_users = []
    # 分批处理
    for i in range(0, len(uid_list), batch_size):
        batch_uids = uid_list[i:i + batch_size]
        try:
            # 调用原有函数
            users = get_weibo_users(batch_uids, cookie)
            all_users.extend(users)
            print(f"成功获取第{int(i / batch_size) + 1}批用户数据，共{len(users)}条")
        except Exception as e:
            print(f"获取第{int(i / batch_size) + 1}批用户数据失败: {str(e)}")
            # 失败时重试一次
            try:
                time.sleep(delay * 2)  # 延长延迟后重试
                users = get_weibo_users(batch_uids)
                all_users.extend(users)
                print(f"重试后成功获取第{int(i / batch_size) + 1}批用户数据")
            except:
                print(f"重试后仍失败，跳过这批用户")

        # 批次之间添加随机延迟，避免被反爬
        if i + batch_size < len(uid_list):
            sleep_time = delay + random.uniform(0, 1)
            time.sleep(sleep_time)

    return all_users