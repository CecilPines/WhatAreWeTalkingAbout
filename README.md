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
# 在项目根目录创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 更新 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

#### 方式二：直接安装

```bash
# 更新 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件设置

在**项目根目录**（与 `backend` 文件夹同级）创建 `.env` 文件。

**方法：**

1. 复制 `.env.example` 文件为 `.env`
2. 根据 `.env.example` 中的示例填写你的配置信息

**注意：**

- `.env` 文件必须创建在**项目根目录**（与 `backend` 文件夹同级）
- `COOKIE` 是你的微博登录 Cookie（必需）
- `WID` 是你要分析的微博 ID（必需，例如：`QbelLys5Z`）
- 所有参数都可以在代码中手动指定，会覆盖 `.env` 文件中的设置

### 3. 使用方法

#### 方式一：直接运行（推荐）

在虚拟环境中直接运行脚本：

```bash
# 确保已激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 运行分析工具
python backend/WeiboDeepAnalyzer.py
```

程序会自动从 `.env` 文件中读取配置（`WID`、`COOKIE`、`DOWNLOAD_IMAGES`、`MAX_COMMENT_PAGES`、`MAX_REPOST_PAGES` 等）。

#### 方式二：使用 API 服务

如果需要通过 API 接口调用：

```bash
# 确保已激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 进入 backend 目录
cd backend

# 启动 API 服务
python api_server.py
# 或者使用 uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

启动后访问 `http://localhost:8000/docs` 查看 API 文档。

#### 方式三：在代码中调用

如果需要在自己的代码中使用：

```python
from backend.WeiboDeepAnalyzer import WeiboDeepAnalyzer

# 方式1：从 .env 文件读取所有配置（推荐）
analyzer = WeiboDeepAnalyzer()  # 所有参数从 .env 读取
analyzer.analyze()  # 页数限制也从 .env 读取

# 方式2：部分参数从 .env 读取，部分手动指定
analyzer = WeiboDeepAnalyzer(download_images=True)
analyzer.analyze(max_comment_pages=5, max_repost_pages=5)

# 方式3：完全手动指定参数
analyzer = WeiboDeepAnalyzer(
    wid='QbelLys5Z',
    cookie='your_cookie_here',
    download_images=False,
    output_dir='my_analysis'
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

- `{微博ID}_complete.json` - 完整数据（JSON 格式）
- `{微博ID}_weibo.csv` - 微博内容
- `{微博ID}_comments.csv` - 评论数据
- `{微博ID}_reposts.csv` - 转发数据
- `{微博ID}_stats.csv` - 统计数据
- `images/` - 图片文件夹（如果启用了图片下载）

## ⚙️ 参数说明

所有参数都可以通过 `.env` 文件配置，也可以在代码中手动指定（会覆盖 `.env` 中的设置）：

### 初始化参数（`WeiboDeepAnalyzer.__init__`）

- `wid`: 微博 ID（可以是数字 ID 或 mid，可选，从 `.env` 的 `WID` 读取）
- `cookie`: 微博 Cookie（可选，从 `.env` 的 `COOKIE` 读取）
- `output_dir`: 输出目录（可选，从 `.env` 的 `OUTPUT_DIR` 读取，默认：`weibo_analysis`）
- `download_images`: 是否下载图片到本地（可选，从 `.env` 的 `DOWNLOAD_IMAGES` 读取，默认：`False`）

### 分析参数（`analyze()` 方法）

- `max_comment_pages`: 评论最大爬取页数（可选，从 `.env` 的 `MAX_COMMENT_PAGES` 读取，`None` 表示全部爬取）
- `max_repost_pages`: 转发最大爬取页数（可选，从 `.env` 的 `MAX_REPOST_PAGES` 读取，`None` 表示全部爬取）

### .env 文件配置项

| 配置项              | 类型   | 必需 | 默认值           | 说明             |
| ------------------- | ------ | ---- | ---------------- | ---------------- |
| `WID`               | 字符串 | ✅   | -                | 微博 ID          |
| `COOKIE`            | 字符串 | ✅   | -                | 微博登录 Cookie  |
| `DOWNLOAD_IMAGES`   | 布尔值 | ❌   | `false`          | 是否下载图片     |
| `MAX_COMMENT_PAGES` | 整数   | ❌   | 无限制           | 评论最大爬取页数 |
| `MAX_REPOST_PAGES`  | 整数   | ❌   | 无限制           | 转发最大爬取页数 |
| `OUTPUT_DIR`        | 字符串 | ❌   | `weibo_analysis` | 输出目录         |

## 📝 注意事项

1. 使用前请确保配置了有效的微博 Cookie
2. 建议使用虚拟环境来管理依赖，避免污染系统环境
3. 爬取大量数据时建议设置 `max_comment_pages` 和 `max_repost_pages` 参数，避免耗时过长
