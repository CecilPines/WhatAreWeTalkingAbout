# Windows PowerShell 环境配置脚本
# 为 plot.py 项目配置 Python 虚拟环境

Write-Host "正在为 plot.py 项目配置环境..." -ForegroundColor Green

# 检查 Python 是否已安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "检测到 Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "错误: 未检测到 Python，请先安装 Python 3.7 或更高版本" -ForegroundColor Red
    exit 1
}

# 创建虚拟环境
Write-Host "创建虚拟环境..." -ForegroundColor Yellow
python -m venv venv

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 升级 pip
Write-Host "升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 安装依赖包
Write-Host "安装依赖包..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "环境配置完成！" -ForegroundColor Green
Write-Host "要运行 plot.py，请先激活虚拟环境：" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "然后运行：" -ForegroundColor Cyan
Write-Host "  python plot.py" -ForegroundColor White
