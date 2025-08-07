#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化流水线 Web应用
提供Web界面和API接口
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import logging
from datetime import datetime
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_development_only')

# 设置Python路径
import sys
import os
from pathlib import Path
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

# 导入路由模块
try:
    from routes.content_fetch_routes import content_fetch_bp
except ImportError as e:
    logger.warning(f"内容采集路由不可用: {e}")
    content_fetch_bp = None

# 导入API模块
try:
    # 确保当前目录在sys.path中
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from api_content_simple import register_content_apis, register_content_pages
except ImportError as e:
    logger.warning(f"内容管理扩展不可用: {e}")
    def register_content_apis(app):
        logger.warning("API模块不可用，跳过注册内容API")
    def register_content_pages(app):
        logger.warning("API模块不可用，跳过注册内容页面")

# 导入管理模块
try:
    from task_manager import TaskManager
    from user_manager import UserManager
    from database import init_db, get_db_connection
except ImportError as e:
    logger.error(f"数据库初始化失败: {e}")
    class TaskManager:
        def __init__(self):
            pass
        def start(self):
            logger.warning("任务管理器不可用")
        def get_stats(self):
            return {"total": 0, "running": 0, "completed": 0, "failed": 0}
        def get_all_tasks(self):
            return []
    
    class UserManager:
        def __init__(self):
            pass
        def get_user_count(self):
            return 0
        def get_all_users(self):
            return []
    
    def init_db():
        logger.warning("数据库初始化不可用")
    
    def get_db_connection():
        logger.warning("数据库连接不可用")
        return None

# 初始化数据库
init_db()

# 初始化任务管理器
task_manager = TaskManager()
task_manager.start()

# 初始化用户管理器
user_manager = UserManager()

# 注册蓝图
app.register_blueprint(content_fetch_bp, url_prefix='/content-fetch')

# 注册内容API和页面
register_content_apis(app)
register_content_pages(app)

# 首页
@app.route('/')
def index():
    """首页"""
    return render_template('dashboard.html', title="视频自动化流水线")

# 仪表盘
@app.route('/dashboard')
def dashboard():
    """仪表盘"""
    # 获取任务统计
    task_stats = task_manager.get_stats()
    
    # 获取用户统计
    user_stats = user_manager.get_user_count()
    
    return render_template(
        'dashboard.html',
        title="仪表盘",
        task_stats=task_stats,
        user_stats=user_stats
    )

# 任务页面
@app.route('/tasks')
def tasks():
    """任务页面"""
    # 获取所有任务
    all_tasks = task_manager.get_all_tasks()
    
    return render_template(
        'tasks.html',
        title="任务管理",
        tasks=all_tasks
    )

# 用户页面
@app.route('/accounts')
def accounts():
    """用户页面"""
    # 获取所有用户
    all_users = user_manager.get_all_users()
    
    return render_template(
        'accounts.html',
        title="用户管理",
        users=all_users
    )

# 帮助页面
@app.route('/help')
def help_page():
    """帮助页面"""
    return render_template('help.html', title="帮助中心")

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    """404错误页面"""
    return render_template('404.html', title="页面未找到"), 404

@app.errorhandler(500)
def server_error(e):
    """500错误页面"""
    return render_template('500.html', title="服务器错误"), 500

# 启动应用
if __name__ == '__main__':
    logger.info("启动Web应用")
    try:
        app.run(debug=True, host='0.0.0.0', port=5003)  # 修改端口为5003
    except OSError as e:
        if "Address already in use" in str(e):
            # 如果端口5003也被占用，尝试使用5004
            print(f"端口5003已被占用，尝试使用端口5004...")
            app.run(debug=True, host='0.0.0.0', port=5004)
        else:
            raise
