#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化系统Web界面 - 简化版
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Flask相关导入
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'video-automation-secret-key-2024'

# 创建SocketIO实例
socketio = SocketIO(app, cors_allowed_origins="*")

# 数据目录
DATA_DIR = project_root / "data"

# 导入项目模块（延迟导入避免循环依赖）
def get_task_manager():
    try:
        from task_manager import TaskManager
        return TaskManager()
    except Exception as e:
        logger.error(f"导入TaskManager失败: {e}")
        return None

def get_user_manager():
    try:
        from user_manager import UserManager
        return UserManager()
    except Exception as e:
        logger.error(f"导入UserManager失败: {e}")
        return None

def get_config_manager():
    try:
        from config_manager import ConfigManager
        return ConfigManager()
    except Exception as e:
        logger.error(f"导入ConfigManager失败: {e}")
        return None

# 导入内容管理扩展
try:
    from api_content_simple import register_content_apis, register_content_pages
    register_content_apis(app)
    register_content_pages(app)
    logger.info("内容管理扩展已注册")
except ImportError as e:
    logger.warning(f"内容管理扩展不可用: {e}")
except Exception as e:
    logger.error(f"注册内容管理扩展失败: {e}")

@app.route('/')
def index():
    """主页"""
    try:
        task_manager = get_task_manager()
        user_manager = get_user_manager()
        
        # 获取系统统计信息
        all_tasks = task_manager.get_all_tasks() if task_manager else []
        all_users = user_manager.get_all_users() if user_manager else []
        
        stats = {
            'total_tasks': len(all_tasks),
            'running_tasks': len([t for t in all_tasks if t.get('status') == 'running']),
            'completed_tasks': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed_tasks': len([t for t in all_tasks if t.get('status') == 'failed']),
            'total_users': len(all_users),
            'active_users': len([u for u in all_users if u.get('status') == 'active'])
        }
        
        # 获取最近的任务
        recent_tasks = all_tasks[-5:] if all_tasks else []
        
        return render_template('dashboard.html', stats=stats, recent_tasks=recent_tasks)
    except Exception as e:
        logger.error(f"渲染主页失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/tasks')
def tasks():
    """任务管理页面"""
    try:
        task_manager = get_task_manager()
        all_tasks = task_manager.get_all_tasks() if task_manager else []
        return render_template('tasks.html', tasks=all_tasks)
    except Exception as e:
        logger.error(f"渲染任务页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/accounts')
def accounts():
    """账号管理页面"""
    try:
        user_manager = get_user_manager()
        all_users = user_manager.get_all_users() if user_manager else []
        return render_template('accounts.html', users=all_users)
    except Exception as e:
        logger.error(f"渲染账号页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/videos')
def videos():
    """视频管理页面"""
    try:
        return render_template('videos.html')
    except Exception as e:
        logger.error(f"渲染视频页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/monitoring')
def monitoring():
    """监控页面"""
    try:
        return render_template('monitoring.html')
    except Exception as e:
        logger.error(f"渲染监控页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/help')
def help_page():
    """帮助页面"""
    try:
        return render_template('help.html')
    except Exception as e:
        logger.error(f"渲染帮助页面失败: {e}")
        return f"页面加载失败: {e}", 500

# API路由
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """API: 获取任务列表"""
    try:
        task_manager = get_task_manager()
        tasks = task_manager.get_all_tasks() if task_manager else []
        return jsonify({
            'success': True,
            'tasks': tasks
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    """API: 创建任务"""
    try:
        task_manager = get_task_manager()
        if not task_manager:
            return jsonify({
                'success': False,
                'error': '任务管理器不可用'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        task_id = task_manager.create_task(
            name=data.get('name', ''),
            task_type=data.get('task_type', ''),
            config=data.get('config', {})
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id
        })
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>', methods=['GET'])
def api_get_task(task_id):
    """API: 获取单个任务"""
    try:
        task_manager = get_task_manager()
        if not task_manager:
            return jsonify({
                'success': False,
                'error': '任务管理器不可用'
            }), 500
        
        task = task_manager.get_task(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'task': task
        })
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/start', methods=['POST'])
def api_start_task(task_id):
    """API: 启动任务"""
    try:
        task_manager = get_task_manager()
        if not task_manager:
            return jsonify({
                'success': False,
                'error': '任务管理器不可用'
            }), 500
        
        success = task_manager.start_task(task_id)
        if success:
            return jsonify({
                'success': True,
                'message': '任务启动成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务启动失败'
            }), 500
    except Exception as e:
        logger.error(f"启动任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """WebSocket连接事件"""
    logger.info(f"客户端连接: {request.sid}")
    emit('connected', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开连接事件"""
    logger.info(f"客户端断开连接: {request.sid}")

@socketio.on('get_system_status')
def handle_get_system_status():
    """获取系统状态"""
    try:
        task_manager = get_task_manager()
        all_tasks = task_manager.get_all_tasks() if task_manager else []
        
        stats = {
            'total_tasks': len(all_tasks),
            'running_tasks': len([t for t in all_tasks if t.get('status') == 'running']),
            'completed_tasks': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed_tasks': len([t for t in all_tasks if t.get('status') == 'failed']),
            'timestamp': datetime.now().isoformat()
        }
        emit('system_status', stats)
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        emit('error', {'message': str(e)})

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return "页面未找到", 404

@app.errorhandler(500)
def internal_error(error):
    return "服务器内部错误", 500

if __name__ == '__main__':
    logger.info("==========================================")
    logger.info("视频自动化系统Web界面")
    logger.info("==========================================")
    logger.info("正在启动Web服务器...")
    logger.info("访问地址: http://localhost:5002")
    logger.info("按 Ctrl+C 停止服务器")
    logger.info("==========================================")
    
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 启动Flask应用
    try:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5002, 
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        sys.exit(1)