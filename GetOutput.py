"""from selenium import webdriver
# 初始化浏览器驱动
driver = webdriver.Chrome()
# 打开网页
driver.get("https://weibo.com/")
# 获取浏览器Cookies
cookies = driver.get_cookies()
# 打印Cookies
for cookie in cookies:
   print(cookie)
# 关闭浏览器
driver.quit()"""

"""
with open("./Spidering/env.txt", "r", encoding="utf-8",errors="ignore") as f:
   line = f.readline()
   while line:
       print(line.strip())
       line = f.readline()
"""

import os

def get_project_root() -> str:
    """返回项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))  # 获取当前文件的绝对路径并取其父目录作为根目录

def get_output_dir() -> str:
    """返回output目录的绝对路径"""
    project_root = get_project_root()
    return os.path.join(project_root, 'WebUI', "static")
