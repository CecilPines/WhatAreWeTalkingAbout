import urllib.request
from Spidering.backend.WeiboDeepAnalyzer import _read_env_value

url = 'https://weibo.com/u/7821907549'

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
    'cookie': _read_env_value('COOKIE'),
}
# 请求对象的定制
request = urllib.request.Request(url=url, headers=headers)
# 模拟浏览器向服务器发送请求
response = urllib.request.urlopen(request)
# 获取响应数据
content = response.read().decode("utf-8")
# 打印响应数据
print(content)
# 下载到本地
with open('./weibo.html', 'w', encoding='utf-8') as fp:
    fp.write(content)