#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频搬运矩阵自动化系统启动脚本
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           视频搬运矩阵自动化系统 v1.0.0                          ║
    ║           Video Auto Pipeline System                         ║
    ║                                                              ║
    ║           🎥 多平台视频自动化处理与发布系统                       ║
    ║           🤖 集成AI智能内容生成                                 ║
    ║           📊 实时数据分析与监控                                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    return True

def check_basic_packages():
    """检查基础包"""
    print("🔍 检查基础依赖...")
    
    basic_packages = ['flask', 'requests']
    missing_packages = []
    
    for package in basic_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少基础包: {', '.join(missing_packages)}")
        print("请运行: pip install flask requests")
        return False
    
    print("✅ 基础依赖检查完成")
    return True

def setup_environment():
    """设置环境"""
    print("🔧 设置运行环境...")
    
    # 创建必要的目录
    directories = [
        'logs', 'uploads', 'temp', 'data', 'static/uploads'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 检查配置文件
    env_file = project_root / '.env'
    if not env_file.exists():
        print("⚠️  未找到.env配置文件，将使用默认配置")
        create_example_env()
    
    print("✅ 环境设置完成")

def create_example_env():
    """创建示例环境配置文件"""
    env_content = """# 数据库配置
DATABASE_URL=sqlite:///data/video_pipeline.db

# AI服务配置（请填入您的API密钥）
OPENAI_API_KEY=your_openai_api_key_here
FLIKI_API_KEY=your_fliki_api_key_here
HEYGEN_API_KEY=your_heygen_api_key_here

# 腾讯云配置（请填入您的密钥）
TENCENT_SECRET_ID=your_secret_id_here
TENCENT_SECRET_KEY=your_secret_key_here
TENCENT_REGION=ap-beijing

# 存储配置
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=2147483648

# 安全配置
SECRET_KEY=your_secret_key_here_please_change_this

# 系统配置
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=5000
"""
    
    with open(project_root / '.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("📝 已创建示例配置文件 .env，请根据需要修改配置")

def init_database():
    """初始化数据库"""
    print("🗄️  初始化数据库...")
    
    try:
        # 简单的SQLite数据库初始化
        import sqlite3
        db_path = project_root / 'data' / 'video_pipeline.db'
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 创建基础表结构
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认管理员账户
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, email) 
            VALUES ('admin', 'admin123', 'admin@example.com')
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def start_web_app():
    """启动Web应用"""
    print("🚀 启动Web应用...")
    
    try:
        # 检查web_app.py是否存在
        web_app_path = project_root / 'web_app.py'
        if not web_app_path.exists():
            print("❌ 未找到web_app.py文件")
            return False
        
        # 启动Flask应用
        os.chdir(project_root)
        os.environ['FLASK_APP'] = 'web_app.py'
        os.environ['FLASK_ENV'] = 'development'
        
        # 直接运行web_app.py
        subprocess.run([sys.executable, 'web_app.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭...")
        return True
    except Exception as e:
        print(f"❌ Web应用启动失败: {e}")
        return False

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n🛑 接收到停止信号，正在关闭系统...")
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查基础包
    if not check_basic_packages():
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 初始化数据库
    if not init_database():
        print("❌ 数据库初始化失败，请检查配置")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 系统准备完成！")
    print("📱 Web界面: http://localhost:5000")
    print("👤 默认账户: admin / admin123")
    print("📖 文档: 请查看 README.md")
    print("🛑 停止系统: Ctrl+C")
    print("="*60 + "\n")
    
    # 启动Web应用
    start_web_app()

if __name__ == "__main__":
    main()