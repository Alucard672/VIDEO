#!/bin/bash

# 视频自动化系统快速启动脚本

echo "=========================================="
echo "视频自动化系统快速启动"
echo "=========================================="

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    
    echo "激活虚拟环境..."
    source venv/bin/activate
    echo "虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "已在虚拟环境中: $VIRTUAL_ENV"
fi

# 检查依赖是否已安装
echo "检查依赖包..."
if ! python -c "import loguru" 2>/dev/null; then
    echo "安装依赖包..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
else
    echo "依赖包已安装"
fi

# 创建必要的目录
echo "创建数据目录..."
mkdir -p data/videos data/audio data/thumbnails data/edited_videos logs

# 运行系统测试
echo "运行系统测试..."
python test_system.py

echo "=========================================="
echo "环境设置完成！"
echo "=========================================="
echo ""
echo "使用方法："
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 运行完整流程: python run_pipeline.py"
echo "3. 运行系统测试: python test_system.py"
echo ""
echo "详细说明请查看: 使用说明.md"
echo "==========================================" 