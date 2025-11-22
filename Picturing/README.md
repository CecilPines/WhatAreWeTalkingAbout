# Plot.py 项目环境配置说明

## 项目简介
这是一个使用 Python 绘制数学函数图像的简单项目，主要绘制 y = x² 函数的图像。

## 依赖包
- matplotlib >= 3.5.0 (用于绘图)
- numpy >= 1.21.0 (用于数值计算)

## 环境配置方法

### 方法一：使用自动配置脚本（推荐）
1. 在 PowerShell 中运行：
   ```powershell
   .\setup_env.ps1
   ```

### 方法二：手动配置
1. 创建虚拟环境：
   ```powershell
   python -m venv venv
   ```

2. 激活虚拟环境：
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. 安装依赖包：
   ```powershell
   pip install -r requirements.txt
   ```

## 运行项目
1. 激活虚拟环境：
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. 运行绘图程序：
   ```powershell
   python plot.py
   ```

## 注意事项
- 需要 Python 3.7 或更高版本
- 确保已安装 matplotlib 后端支持（通常会自动安装）
- 如果遇到显示问题，可能需要安装额外的图形界面支持

## 项目文件说明
- `plot.py`: 主程序文件，绘制 y = x² 函数图像
- `requirements.txt`: 项目依赖包列表
- `setup_env.ps1`: 自动环境配置脚本

