# WeiboDeepAnalyzer 快速开始指南

## ? 5 分钟上手

### 第一步：安装依赖

```bash
pip install requests lxml pillow
```

### 第二步：配置 Cookie

在`无 GUI 功能独立版/`目录下创建`.env`文件：

```
COOKIE=你的微博Cookie字符串
```

**如何获取 Cookie？**

1. 浏览器访问 https://weibo.cn 并登录
2. 按 F12 打开开发者工具 → Network 标签
3. 刷新页面 → 点击任意请求
4. 复制 Request Headers 中的 Cookie 值

### 第三步：运行示例

**方法 1：使用测试脚本（推荐）**

```bash
cd "无 GUI 功能独立版"
python test_deep_analyzer.py
```

选择"1"进行快速测试，或选择"4"进行自定义测试。

**方法 2：编写自己的代码**

```python
from WeiboDeepAnalyzer import WeiboDeepAnalyzer

# 完整分析（限制评论和转发各10页）
analyzer = WeiboDeepAnalyzer(wid='你的微博ID')
analyzer.analyze(max_comment_pages=10, max_repost_pages=10)

print(f"分析完成！结果保存在: {analyzer.wid_dir}")
```

---

## ? 获取微博 ID 的方法

### 方法 1：从微博链接提取

- 手机端：`https://m.weibo.cn/status/QbelLys5Z` → ID 是 `QbelLys5Z`
- PC 端：`https://weibo.com/1234567890/QbelLys5Z` → ID 是 `QbelLys5Z`

### 方法 2：从评论页面

访问微博详情，浏览器地址栏中：

- `https://weibo.cn/comment/QbelLys5Z` → ID 是 `QbelLys5Z`

---

## ? 输出文件说明

分析完成后会在 `weibo_analysis/{微博ID}/` 生成以下文件：

```
weibo_analysis/
└── QbelLys5Z/
    ├── QbelLys5Z_complete.json    # 完整JSON数据
    ├── QbelLys5Z_weibo.csv        # 微博基本信息
    ├── QbelLys5Z_comments.csv     # 评论详情
    ├── QbelLys5Z_reposts.csv      # 转发详情
    └── QbelLys5Z_stats.csv        # 统计数据
```

---

## ? 常见用法

### 1. 快速测试（小数据量）

```python
analyzer = WeiboDeepAnalyzer(wid='微博ID')
analyzer.analyze(max_comment_pages=5, max_repost_pages=5)
```

### 2. 完整分析（所有数据）

```python
analyzer = WeiboDeepAnalyzer(wid='微博ID')
analyzer.analyze()  # 不限制页数，爬取全部
```

### 3. 只获取评论

```python
analyzer = WeiboDeepAnalyzer(wid='微博ID')
analyzer.get_weibo_content()
analyzer.get_all_comments(max_pages=20)
analyzer.export_json()
```

### 4. 批量分析多条微博

```python
wids = ['wid1', 'wid2', 'wid3']
for wid in wids:
    analyzer = WeiboDeepAnalyzer(wid=wid)
    analyzer.analyze(max_comment_pages=10, max_repost_pages=10)
    time.sleep(10)  # 避免请求过快
```

---

## ?? 重要提示

### 1. Cookie 相关

- Cookie 会过期，遇到登录提示需重新获取
- 不要分享你的 Cookie 给他人
- 建议使用小号进行数据采集

### 2. 爬取限制

- 请求过快会被限制，建议：
  - 单次分析后间隔 10 秒以上
  - 夜间时段成功率更高
  - 关闭 VPN
- 超热门微博建议限制页数

### 3. 常见错误

**"COOKIE 为空"**

- 检查.env 文件是否正确创建
- 检查 Cookie 格式是否有引号

**"无法访问微博页面"**

- Cookie 已过期，需重新获取
- 微博 ID 不存在或已删除

**"HTTP 302/403"**

- 请求过快被限制，等待 10 分钟后重试
- Cookie 失效

---

## ? 性能参考

| 数据规模 | 评论页数 | 转发页数 | 预计耗时 |
| -------- | -------- | -------- | -------- |
| 测试     | 5        | 5        | 1 分钟   |
| 小型     | 10       | 10       | 2 分钟   |
| 中型     | 50       | 50       | 10 分钟  |
| 大型     | 100+     | 100+     | 30 分钟+ |

---

## ? 更多信息

- 详细文档：[WeiboDeepAnalyzer_README.md](WeiboDeepAnalyzer_README.md)
- 测试脚本：[test_deep_analyzer.py](test_deep_analyzer.py)
- 主程序：[WeiboDeepAnalyzer.py](WeiboDeepAnalyzer.py)

---

## ? 下一步

1. **数据分析**：使用 pandas 读取 CSV 文件进行数据分析

   ```python
   import pandas as pd
   df = pd.read_csv('weibo_analysis/QbelLys5Z/QbelLys5Z_comments.csv')
   print(df.head())
   ```

2. **文本分析**：对评论内容进行情感分析、关键词提取等

3. **可视化**：使用 matplotlib 或 seaborn 绘制互动趋势图

4. **扩展功能**：基于现有代码添加自定义功能

---

**开始探索吧！** ?
