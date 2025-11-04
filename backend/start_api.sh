#!/bin/bash
# -*- coding: utf-8 -*-
"""
FastAPI 服务启动脚本
"""

echo "=========================================="
echo "微博深度分析 API 服务启动"
echo "=========================================="

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未检测到虚拟环境，正在激活..."
    if [ -d "../venv" ]; then
        source ../venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ 未找到虚拟环境，请先创建虚拟环境"
        exit 1
    fi
fi

# 检查依赖
echo "检查依赖..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    pip install fastapi uvicorn
fi

# 启动服务
echo ""
echo "启动服务..."
echo "API 文档地址: http://localhost:8000/docs"
echo "健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

