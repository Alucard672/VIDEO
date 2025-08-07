#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 一键启动视频自动化处理系统
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🎥 视频自动化处理系统 v2.0                           ║
    ║           Video Auto Pipeline System                         ║
    ║                                                              ║
    ║           ✨ 全新内容采集功能                                  ║
    ║           🤖 智能内容管理                                      ║
    ║           📊 实时监控面板                                      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    # 检查必要的包
    required_packages = ['flask', 'requests', 'sqlite3']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install flask requests")
        return False
    
    return True

def setup_directories():
    """设置必要的目录"""
    print("📁 设置目录结构...")
    
    directories = [
        'data',
        'logs',
        'uploads',
        'temp',
        'static/uploads'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}/ 目录已准备")

def init_database():
    """初始化数据库"""
    print("🗄️  初始化数据库...")
    
    try:
        from database import init_database
        init_database()
        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def init_content_fetch_config():
    """初始化内容采集配置"""
    print("⚙️  初始化内容采集配置...")
    
    try:
        from content_fetch_config import ContentFetchConfig
        config = ContentFetchConfig()
        
        # 获取配置信息
        sources = config.get_sources()
        categories = config.get_categories()
        
        print(f"✅ 采集源配置完成 ({len(sources)} 个源)")
        print(f"✅ 分类配置完成 ({len(categories)} 个分类)")
        return True
    except Exception as e:
        print(f"❌ 内容采集配置失败: {e}")
        return False

def start_web_application():
    """启动Web应用"""
    print("🚀 启动Web应用...")
    
    try:
        # 启动Flask应用
        from web_app import app, socketio
        
        print("\n" + "="*60)
        print("🎉 系统启动成功！")
        print("="*60)
        print("📱 Web界面: http://localhost:5002")
        print("🏠 仪表板: http://localhost:5002/")
        print("📥 内容采集: http://localhost:5002/content-fetch")
        print("📄 内容管理: http://localhost:5002/content")
        print("📊 任务管理: http://localhost:5002/tasks")
        print("👤 账号管理: http://localhost:5002/accounts")
        print("📹 视频管理: http://localhost:5002/videos")
        print("📈 系统监控: http://localhost:5002/monitoring")
        print("="*60)
        print("🛑 按 Ctrl+C 停止系统")
        print("="*60)
        
        # 启动服务器
        socketio.run(
            app,
            host='0.0.0.0',
            port=5002,
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭系统...")
        return True
    except Exception as e:
        print(f"❌ Web应用启动失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        sys.exit(1)
    
    # 设置目录
    setup_directories()
    
    # 初始化数据库
    if not init_database():
        print("\n❌ 数据库初始化失败，请检查权限和磁盘空间")
        sys.exit(1)
    
    # 初始化内容采集配置
    if not init_content_fetch_config():
        print("\n⚠️  内容采集配置初始化失败，但系统仍可运行")
    
    print("\n✅ 系统初始化完成！")
    time.sleep(2)
    
    # 启动Web应用
    start_web_application()
    
    print("\n👋 系统已关闭，再见！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 启动中断，再见！")
    except Exception as e:
        print(f"\n❌ 启动过程中出现错误: {e}")
        sys.exit(1)