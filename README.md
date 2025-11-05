# 微博深度分析工具 (WeiboDeepAnalyzer)

单条微博深度分析工具 - 整合内容、评论、转发的完整分析

## 📋 项目说明

### 核心代码文件

**重要提示：**
- **核心功能代码只在 `backend/WeiboDeepAnalyzer.py` 这一个文件中**
- `api_server.py` 是可选的文件，如果不想使用 API 服务，就不需要用到
- 其他代码文件（如 `(using)WeiboRepostSpider.py`、`(using)WeiboUserScrapy.py` 等）只是参考代码，不是必需的

## 🚀 快速开始

### 1. 环境配置

#### 方式一：使用虚拟环境（推荐）

如果不想在自己的电脑中直接安装依赖包，可以使用虚拟环境：

```bash
# 进入 backend 目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 方式二：直接安装

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置文件设置

在 `backend` 文件夹中创建 `.env` 文件，添加以下内容：

```env
# 微博 Cookie（必需）
COOKIE=your_cookie_here

# 微博 ID（必需）
WID=QbelLys5Z
```

**注意：**
- `.env` 文件必须创建在 `backend` 文件夹里面
- `COOKIE` 是你的微博登录 Cookie
- `WID` 是你要分析的微博 ID（例如：`QbelLys5Z`）

### 3. 使用方法

```python
from backend.WeiboDeepAnalyzer import WeiboDeepAnalyzer

# 方式1：从 .env 文件读取配置（推荐）
analyzer = WeiboDeepAnalyzer(download_images=False)
analyzer.analyze(max_comment_pages=10, max_repost_pages=10)

# 方式2：直接指定参数
analyzer = WeiboDeepAnalyzer(
    wid='QbelLys5Z',
    cookie='your_cookie_here',
    download_images=False
)
analyzer.analyze(max_comment_pages=10, max_repost_pages=10)
```

## 📊 功能特性

- ✅ 提取微博完整内容（文字、图片、视频等）
- ✅ 爬取所有评论及回复层级
- ✅ 爬取所有转发信息
- ✅ 生成互动统计分析
- ✅ 输出结构化数据（JSON + CSV）
- ✅ 支持图片下载（可选）

## 📁 输出文件

分析结果会保存在 `backend/weibo_analysis/{微博ID}/` 目录下：

- `{微博ID}_complete.json` - 完整数据（JSON格式）
- `{微博ID}_weibo.csv` - 微博内容
- `{微博ID}_comments.csv` - 评论数据
- `{微博ID}_reposts.csv` - 转发数据
- `{微博ID}_stats.csv` - 统计数据
- `images/` - 图片文件夹（如果启用了图片下载）

## ⚙️ 参数说明

- `wid`: 微博ID（可以是数字ID或mid）
- `cookie`: 微博Cookie（可选，可从环境变量读取）
- `output_dir`: 输出目录（默认：`weibo_analysis`）
- `download_images`: 是否下载图片到本地（默认：`False`）
- `max_comment_pages`: 评论最大爬取页数（`None` 表示全部爬取）
- `max_repost_pages`: 转发最大爬取页数（`None` 表示全部爬取）

## 📝 注意事项

1. 使用前请确保配置了有效的微博 Cookie
2. 建议使用虚拟环境来管理依赖，避免污染系统环境
3. 爬取大量数据时建议设置 `max_comment_pages` 和 `max_repost_pages` 参数，避免耗时过长
