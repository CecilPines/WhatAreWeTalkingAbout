from Picturing.test import batch_get_weibo_users
from Picturing.read_users_json import extract_user_features
from Picturing.user_pic import batch_user_profile_analysis


def get_weibo_users_pic(weibo_uid_list):
    # 根据uid爬取用户信息，并存储在user_ulist列表中，用户信息为json格式
    user_list = batch_get_weibo_users(weibo_uid_list)
    # print(user_list)
    # 从用户爬取数据中提取画像特征
    user_profiles = [extract_user_features(user) for user in user_list]
    print(user_profiles)
    # 将特征传递给大模型，大模型1个txt文件，即用户画像分析结果
    # batch_user_profile_analysis("sk-fe35d14176d74c33892f2dfe011b58e0", user_profiles)
    return user_profiles



if __name__ == '__main__':
    weibo_uid_list = [5238869367,7904512652,7756485110,7756485110,5546364752]
    get_weibo_users_pic(weibo_uid_list)
