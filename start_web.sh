#!/bin/bash

echo "=========================================="
echo "视频自动化系统 - Web界面启动脚本"
echo "=========================================="

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "错误：虚拟环境不存在，请先创建虚拟环境"
    echo "运行命令：python3 -m venv .venv"
    exit 1
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source .venv/bin/activate

# 检查并安装依赖
echo "检查依赖包..."
if ! python -c "import flask" 2>/dev/null; then
    echo "安装基本依赖..."
    pip install Flask requests python-dotenv
fi

# 切换到项目目录
cd video-auto-pipeline

# 启动Web应用
echo "启动Web应用..."
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
echo "=========================================="

python simple_web.py 