#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化系统Web界面
基于环境配置的Flask Web应用
"""

import os
import sys
import subprocess
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
import psutil
import threading
import time
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 导入配置和管理器
try:
    from config import (
        DATABASE_PATH, DATA_DIR, security_config, system_config,
        storage_config, monitoring_config
    )
    from config.environment import get_config
    from task_manager import TaskManager
    from user_manager import UserManager
    from config_manager import ConfigManager
    
    # 获取环境配置
    env_config = get_config()
    
except ImportError as e:
    logger.warning(f"导入模块失败: {e}")
    # 如果模块不存在，创建基本配置
    DATABASE_PATH = project_root / "data" / "system.db"
    DATA_DIR = project_root / "data"
    
    class MockConfig:
        SECRET_KEY = 'dev-secret-key'
        DEBUG = True
        HOST = '0.0.0.0'
        PORT = 5000
    
    security_config = MockConfig()
    system_config = MockConfig()
    storage_config = MockConfig()
    monitoring_config = MockConfig()
    
    class TaskManager:
        def get_recent_tasks(self, limit=10):
            return []
        def get_task_stats(self):
            return {'today_tasks': 0, 'running_tasks': 0, 'completed_tasks': 0}
        def create_task(self, task_data):
            return {'id': 1, 'status': 'created'}
    
    class UserManager:
        def get_current_user(self):
            return {'username': '管理员', 'role': 'admin'}
    
    class ConfigManager:
        def get_config(self, key, default=None):
            return default
        def set_config(self, key, value):
            pass
    
    env_config = None

# 创建Flask应用
app = Flask(__name__)
app.secret_key = security_config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = getattr(storage_config, 'MAX_CONTENT_LENGTH', 16 * 1024 * 1024)

# 配置Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化管理器
task_manager = TaskManager()
user_manager = UserManager()
config_manager = ConfigManager()

# 全局变量存储系统状态
system_metrics = {
    'cpu_percent': 0,
    'memory_percent': 0,
    'disk_percent': 0,
    'timestamp': datetime.now().isoformat()
}

def get_system_metrics():
    """获取系统指标"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"获取系统指标失败: {e}")
        return system_metrics

def background_monitor():
    """后台监控线程"""
    while True:
        try:
            metrics = get_system_metrics()
            system_metrics.update(metrics)
            
            # 通过Socket.IO发送实时数据
            socketio.emit('system_metrics', metrics)
            
            time.sleep(5)  # 每5秒更新一次
        except Exception as e:
            print(f"后台监控错误: {e}")
            time.sleep(10)

# 启动后台监控线程
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

@app.route('/')
def dashboard():
    """仪表板页面"""
    try:
        # 获取统计数据
        stats = task_manager.get_task_stats()
        recent_tasks = task_manager.get_recent_tasks(limit=5)
        current_user = user_manager.get_current_user()
        
        # 模拟通知数据
        notifications = [
            {
                'type': 'info',
                'icon': 'info-circle',
                'title': '系统启动',
                'message': '视频自动化系统已成功启动',
                'time': datetime.now().strftime('%H:%M')
            },
            {
                'type': 'success',
                'icon': 'check-circle',
                'title': '任务完成',
                'message': '内容采集任务已完成',
                'time': (datetime.now() - timedelta(minutes=10)).strftime('%H:%M')
            }
        ]
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_tasks=recent_tasks,
                             notifications=notifications,
                             current_user=current_user)
    except Exception as e:
        print(f"仪表板加载错误: {e}")
        return render_template('dashboard.html', 
                             stats={'today_tasks': 0, 'running_tasks': 0, 'today_videos': 0},
                             recent_tasks=[],
                             notifications=[],
                             current_user={'username': '游客'})

@app.route('/tasks')
def tasks():
    """任务管理页面"""
    try:
        tasks = task_manager.get_recent_tasks(limit=50)
        return render_template('tasks.html', tasks=tasks)
    except Exception as e:
        print(f"任务页面加载错误: {e}")
        return render_template('tasks.html', tasks=[])

@app.route('/videos')
def videos():
    """视频管理页面"""
    try:
        # 模拟视频数据
        videos = []
        video_dir = DATA_DIR / "edited_videos"
        if video_dir.exists():
            for video_file in video_dir.glob("*.mp4"):
                videos.append({
                    'id': len(videos) + 1,
                    'title': video_file.stem,
                    'filename': video_file.name,
                    'size': video_file.stat().st_size if video_file.exists() else 0,
                    'duration': '00:02:30',  # 模拟时长
                    'status': 'completed',
                    'created_time': datetime.fromtimestamp(video_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S') if video_file.exists() else '',
                    'platforms': []
                })
        
        return render_template('videos.html', videos=videos)
    except Exception as e:
        print(f"视频页面加载错误: {e}")
        return render_template('videos.html', videos=[])

@app.route('/accounts')
def accounts():
    """账号管理页面"""
    try:
        # 模拟账号数据
        accounts = [
            {
                'id': 1,
                'platform': 'douyin',
                'username': 'test_account_1',
                'status': 'active',
                'last_login': '2024-01-15 10:30:00',
                'video_count': 25,
                'group_name': '主账号组'
            },
            {
                'id': 2,
                'platform': 'bilibili',
                'username': 'test_account_2',
                'status': 'inactive',
                'last_login': '2024-01-14 15:20:00',
                'video_count': 12,
                'group_name': '备用账号组'
            }
        ]
        
        return render_template('accounts.html', accounts=accounts)
    except Exception as e:
        print(f"账号页面加载错误: {e}")
        return render_template('accounts.html', accounts=[])

@app.route('/monitoring')
def monitoring():
    """系统监控页面"""
    return render_template('monitoring.html', metrics=system_metrics)

@app.route('/config')
def config():
    """系统配置页面"""
    return render_template('config.html')

# API路由
@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API: 获取仪表板统计数据"""
    try:
        stats = task_manager.get_task_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/recent-tasks')
def api_recent_tasks():
    """API: 获取最近任务"""
    try:
        tasks = task_manager.get_recent_tasks(limit=10)
        return jsonify({'tasks': tasks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def api_system_status():
    """API: 获取系统状态"""
    return jsonify({
        'is_running': True,
        'current_task': '',
        'progress': 0
    })

@app.route('/api/system_info')
def api_system_info():
    """API: 获取系统信息"""
    try:
        # 检查Python版本
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        python_version = result.stdout.strip()
    except:
        python_version = '未知'
    
    # 检查虚拟环境
    venv_status = '已激活' if os.environ.get('VIRTUAL_ENV') else '未激活'
    
    # 检查磁盘空间
    try:
        import shutil
        total, used, free = shutil.disk_usage(project_root)
        disk_space = f"总空间: {total // (1024**3)}GB, 可用: {free // (1024**3)}GB"
    except:
        disk_space = '未知'
    
    return jsonify({
        'python_version': python_version,
        'venv_status': venv_status,
        'disk_space': disk_space,
        'dependencies': []
    })

@app.route('/api/monitoring/current-metrics')
def api_current_metrics():
    """API: 获取当前系统指标"""
    return jsonify(system_metrics)

@app.route('/api/tasks', methods=['GET', 'POST'])
def api_tasks():
    """API: 任务管理"""
    if request.method == 'GET':
        try:
            tasks = task_manager.get_recent_tasks(limit=50)
            return jsonify({'tasks': tasks})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            task_data = request.get_json()
            result = task_manager.create_task(task_data)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def api_task_detail(task_id):
    """API: 任务详情操作"""
    if request.method == 'GET':
        # 获取任务详情
        return jsonify({'id': task_id, 'status': 'running'})
    
    elif request.method == 'PUT':
        # 更新任务
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # 删除任务
        return jsonify({'success': True})

@app.route('/api/run_test', methods=['POST'])
def api_run_test():
    """API: 运行测试"""
    try:
        # 运行系统测试
        test_script = project_root / "test_system.py"
        if test_script.exists():
            result = subprocess.run(
                ['python', str(test_script)],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            return jsonify({
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            })
        else:
            return jsonify({
                'success': False,
                'output': '',
                'error': '测试脚本不存在'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'output': '',
            'error': str(e)
        })

@app.route('/api/maintenance', methods=['POST'])
def api_maintenance():
    """API: 系统维护"""
    try:
        # 这里可以添加系统维护逻辑
        # 比如清理临时文件、优化数据库等
        
        return jsonify({
            'success': True,
            'message': '系统维护任务已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Socket.IO事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    print('客户端已连接')
    emit('connected', {'data': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接事件"""
    print('客户端已断开连接')

@socketio.on('request_metrics')
def handle_request_metrics():
    """请求系统指标"""
    emit('system_metrics', system_metrics)

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("==========================================")
    print("视频自动化系统Web界面")
    print("==========================================")
    print("正在启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("==========================================")
    
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 启动Flask应用
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)