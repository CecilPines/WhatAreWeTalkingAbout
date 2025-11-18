from Picturing.get_weibo_users import get_weibo_users
from Picturing.read_users_json import extract_user_features
from Picturing.user_pic import batch_user_profile_analysis
import os

def get_weibo_users_pic(weibo_uid_list):
    # 根据uid爬取用户信息，并存储在user_ulist列表中，用户信息为json格式
    user_list = get_weibo_users(weibo_uid_list)
    # print(user_list[0])

    # 将特征传递给大模型，大模型1个txt文件，即用户画像分析结果
    analysis = batch_user_profile_analysis("sk-fe35d14176d74c33892f2dfe011b58e0", user_list)
    return analysis

if __name__ == '__main__':
    weibo_uid_list = []
    dir = os.getcwd()
    with open(dir + "\\id.txt", encoding="utf-8", mode="r") as f:
        for line in f:
            weibo_uid_list.append(line.strip('\n'))


    analysis = get_weibo_users_pic(weibo_uid_list)
