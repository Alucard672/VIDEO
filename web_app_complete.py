#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化系统Web界面 - 完整版
包含所有内容管理和素材处理功能
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
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

def get_content_storage():
    try:
        from content_storage import content_storage
        return content_storage
    except Exception as e:
        logger.error(f"导入ContentStorage失败: {e}")
        return None

def get_content_processor():
    try:
        from content_processor import content_processor
        return content_processor
    except Exception as e:
        logger.error(f"导入ContentProcessor失败: {e}")
        return None

# ==================== 主要页面路由 ====================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """主页/仪表板"""
    try:
        task_manager = get_task_manager()
        user_manager = get_user_manager()
        content_storage = get_content_storage()
        
        # 获取系统统计信息
        all_tasks = task_manager.get_recent_tasks() if task_manager else []
        all_users = user_manager.get_all_users() if user_manager else []
        
        # 获取内容统计
        content_stats = content_storage.get_content_statistics() if content_storage else {}
        total_stats = content_stats.get('total_stats', {})
        
        stats = {
            'total_tasks': len(all_tasks),
            'running_tasks': len([t for t in all_tasks if t.get('status') == 'running']),
            'completed_tasks': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed_tasks': len([t for t in all_tasks if t.get('status') == 'failed']),
            'total_users': len(all_users),
            'active_users': len([u for u in all_users if u.get('status') == 'active']),
            'total_articles': total_stats.get('total_articles', 0),
            'processed_articles': total_stats.get('processed_articles', 0),
            'total_words': total_stats.get('total_words', 0)
        }
        
        # 获取最近的任务
        recent_tasks = all_tasks[-5:] if all_tasks else []
        
        # 获取最近的文章
        recent_articles = content_storage.get_recent_articles(5) if content_storage else []
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_tasks=recent_tasks,
                             recent_articles=recent_articles)
    except Exception as e:
        logger.error(f"渲染主页失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/tasks')
def tasks():
    """任务管理页面"""
    try:
        task_manager = get_task_manager()
        all_tasks = task_manager.get_recent_tasks() if task_manager else []
        
        # 计算任务统计
        stats = {
            'today_tasks': len(all_tasks),
            'running_tasks': len([t for t in all_tasks if t.get('status') == 'running']),
            'completed_tasks': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed_tasks': len([t for t in all_tasks if t.get('status') == 'failed'])
        }
        
        return render_template('tasks.html', tasks=all_tasks, stats=stats)
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
        # 获取系统指标（模拟数据）
        import psutil
        
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_speed': 0  # 网络速度需要单独计算
        }
        
        return render_template('monitoring.html', metrics=metrics)
    except Exception as e:
        logger.error(f"渲染监控页面失败: {e}")
        # 如果psutil不可用，使用默认值
        metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'network_speed': 0
        }
        return render_template('monitoring.html', metrics=metrics)

@app.route('/help')
def help_page():
    """帮助页面"""
    try:
        return render_template('help.html')
    except Exception as e:
        logger.error(f"渲染帮助页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/analytics')
def analytics_page():
    """分析页面"""
    try:
        task_manager = get_task_manager()
        content_storage = get_content_storage()
        
        # 获取基础统计数据
        all_tasks = task_manager.get_recent_tasks() if task_manager else []
        content_stats = content_storage.get_content_statistics() if content_storage else {}
        
        # 计算任务统计
        task_stats = {
            'total': len(all_tasks),
            'completed': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed': len([t for t in all_tasks if t.get('status') == 'failed']),
            'success_rate': 0
        }
        
        if task_stats['total'] > 0:
            task_stats['success_rate'] = task_stats['completed'] / task_stats['total']
        
        # 获取内容统计
        total_stats = content_stats.get('total_stats', {})
        category_stats = content_stats.get('category_stats', [])
        source_stats = content_stats.get('source_stats', [])
        
        # 准备模板数据
        template_data = {
            'task_stats': task_stats,
            'content_stats': total_stats,
            'category_stats': category_stats,
            'source_stats': source_stats
        }
        
        return render_template('analytics_minimal.html', **template_data)
        
    except Exception as e:
        logger.error(f"渲染分析页面失败: {e}")
        import traceback
        traceback.print_exc()
        return f"页面加载失败: {e}", 500

@app.route('/reports')
def reports_page():
    """报告页面"""
    try:
        # 获取报告数据
        reports = [
            {
                'id': 1,
                'name': '任务执行报告',
                'type': 'task_report',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            },
            {
                'id': 2,
                'name': '内容统计报告',
                'type': 'content_report',
                'created_at': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            }
        ]
        
        return render_template('reports.html', reports=reports)
        
    except Exception as e:
        logger.error(f"渲染报告页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/config')
def config_page():
    """配置页面"""
    try:
        # 获取配置信息
        config_sections = [
            {
                'name': '系统配置',
                'items': [
                    {'key': 'system.debug', 'value': 'false', 'description': '调试模式'},
                    {'key': 'system.log_level', 'value': 'INFO', 'description': '日志级别'}
                ]
            },
            {
                'name': 'API配置',
                'items': [
                    {'key': 'api.timeout', 'value': '30', 'description': 'API超时时间(秒)'},
                    {'key': 'api.retry_count', 'value': '3', 'description': '重试次数'}
                ]
            }
        ]
        
        return render_template('config.html', config_sections=config_sections)
        
    except Exception as e:
        logger.error(f"渲染配置页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/logs')
def logs_page():
    """日志页面"""
    try:
        # 创建简单的日志条目
        log_entries = [
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '系统正常运行中'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': 'Web服务器启动成功'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '任务管理器初始化完成'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '内容存储系统初始化完成'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=4)).strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '用户管理系统初始化完成'
            }
        ]
        
        return render_template('logs_minimal.html', log_entries=log_entries)
        
    except Exception as e:
        logger.error(f"渲染日志页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/users')
def users_page():
    """用户管理页面"""
    try:
        user_manager = get_user_manager()
        users = user_manager.get_all_users() if user_manager else []
        
        return render_template('users.html', users=users)
        
    except Exception as e:
        logger.error(f"渲染用户页面失败: {e}")
        return f"页面加载失败: {e}", 500

# ==================== 内容管理页面 ====================

@app.route('/content')
def content_management():
    """内容管理页面"""
    try:
        content_storage = get_content_storage()
        if not content_storage:
            return "内容存储系统不可用", 500
        
        # 获取内容统计
        stats = content_storage.get_content_statistics()
        
        # 获取最近的文章
        recent_articles = content_storage.get_recent_articles(20)
        
        return render_template('content.html', 
                             stats=stats.get('total_stats', {}),
                             category_stats=stats.get('category_stats', []),
                             source_stats=stats.get('source_stats', []),
                             recent_articles=recent_articles)
    except Exception as e:
        logger.error(f"渲染内容管理页面失败: {e}")
        return f"页面加载失败: {e}", 500

@app.route('/content/view/<task_id>')
def content_view_by_task(task_id):
    """查看特定任务的采集内容"""
    try:
        content_storage = get_content_storage()
        task_manager = get_task_manager()
        
        if not content_storage or not task_manager:
            return "系统组件不可用", 500
        
        # 获取任务信息
        task = task_manager.get_task(task_id)
        if not task:
            return "任务不存在", 404
        
        # 获取任务相关的内容
        articles = content_storage.get_articles_by_task(task_id)
        
        # 获取统计信息
        stats = {
            'total_articles': len(articles),
            'total_words': sum(article.get('word_count', 0) for article in articles),
            'categories': list(set(article.get('category', '未分类') for article in articles)),
            'sources': list(set(article.get('source', '') for article in articles if article.get('source')))
        }
        
        return render_template('content_view.html',
                             task=task,
                             articles=articles,
                             stats=stats)
    except Exception as e:
        logger.error(f"内容查看页面加载错误: {e}")
        return f"页面加载错误: {str(e)}", 500

@app.route('/content/article/<article_id>')
def article_detail_page(article_id):
    """文章详情页面"""
    try:
        content_storage = get_content_storage()
        if not content_storage:
            return "内容存储系统不可用", 500
        
        article = content_storage.get_article_by_id(article_id)
        if not article:
            return "文章不存在", 404
        
        return render_template('article_detail.html', article=article)
    except Exception as e:
        logger.error(f"文章详情页面加载错误: {e}")
        return f"页面加载错误: {str(e)}", 500

# ==================== 任务管理API ====================

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """API: 获取任务列表"""
    try:
        task_manager = get_task_manager()
        tasks = task_manager.get_recent_tasks() if task_manager else []
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

# ==================== 仪表板API ====================

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API: 获取仪表板统计数据"""
    try:
        task_manager = get_task_manager()
        user_manager = get_user_manager()
        content_storage = get_content_storage()
        
        # 获取任务统计
        all_tasks = task_manager.get_recent_tasks() if task_manager else []
        task_stats = {
            'total': len(all_tasks),
            'running': len([t for t in all_tasks if t.get('status') == 'running']),
            'completed': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed': len([t for t in all_tasks if t.get('status') == 'failed'])
        }
        
        # 获取用户统计
        all_users = user_manager.get_all_users() if user_manager else []
        user_stats = {
            'total': len(all_users),
            'active': len([u for u in all_users if u.get('status') == 'active'])
        }
        
        # 获取内容统计
        content_stats = content_storage.get_content_statistics() if content_storage else {}
        total_stats = content_stats.get('total_stats', {})
        
        return jsonify({
            'success': True,
            'stats': {
                'tasks': task_stats,
                'users': user_stats,
                'content': {
                    'total_articles': total_stats.get('total_articles', 0),
                    'processed_articles': total_stats.get('processed_articles', 0),
                    'total_words': total_stats.get('total_words', 0)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取仪表板统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/recent-tasks')
def api_recent_tasks():
    """API: 获取最近的任务"""
    try:
        task_manager = get_task_manager()
        if not task_manager:
            return jsonify({'success': False, 'error': '任务管理器不可用'}), 500
        
        recent_tasks = task_manager.get_recent_tasks(limit=10)
        return jsonify({'success': True, 'tasks': recent_tasks})
        
    except Exception as e:
        logger.error(f"获取最近任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitoring/current-metrics')
def api_current_metrics():
    """API: 获取当前系统指标"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            'cpu': {'percent': cpu_percent, 'cores': psutil.cpu_count()},
            'memory': {'percent': memory.percent, 'used': memory.used, 'total': memory.total},
            'disk': {'percent': disk.percent, 'used': disk.used, 'total': disk.total},
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'metrics': metrics})
        
    except ImportError:
        # 如果psutil不可用，返回模拟数据
        metrics = {
            'cpu': {'percent': 0, 'cores': 4},
            'memory': {'percent': 0, 'used': 0, 'total': 8589934592},
            'disk': {'percent': 0, 'used': 0, 'total': 1000000000000},
            'timestamp': datetime.now().isoformat()
        }
        return jsonify({'success': True, 'metrics': metrics})
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 账号管理API ====================

@app.route('/api/accounts')
def api_get_accounts():
    """API: 获取账号列表"""
    try:
        user_manager = get_user_manager()
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器不可用'}), 500
        
        users = user_manager.get_all_users()
        return jsonify({'success': True, 'accounts': users, 'total': len(users)})
        
    except Exception as e:
        logger.error(f"获取账号列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts/statistics')
def api_accounts_statistics():
    """API: 获取账号统计"""
    try:
        user_manager = get_user_manager()
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器不可用'}), 500
        
        users = user_manager.get_all_users()
        stats = {
            'total': len(users),
            'active': len([u for u in users if u.get('status') == 'active']),
            'inactive': len([u for u in users if u.get('status') != 'active']),
            'platforms': {}
        }
        
        # 统计各平台账号数量
        for user in users:
            platform = user.get('platform', '未知')
            stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
        
        return jsonify({'success': True, 'statistics': stats})
        
    except Exception as e:
        logger.error(f"获取账号统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 内容管理API ====================

@app.route('/api/content')
def api_get_content():
    """API: 获取内容列表"""
    try:
        content_storage = get_content_storage()
        if not content_storage:
            return jsonify({
                'success': False,
                'error': '内容存储系统不可用'
            }), 500
        
        # 获取查询参数
        category = request.args.get('category')
        source = request.args.get('source')
        status = request.args.get('status')
        task_id = request.args.get('task_id')
        limit = int(request.args.get('limit', 50))
        
        # 获取内容
        if task_id:
            articles = content_storage.get_articles_by_task(task_id)
        else:
            articles = content_storage.get_recent_articles(
                limit=limit, 
                category=category, 
                status=status
            )
        
        # 如果指定了来源，进行过滤
        if source:
            articles = [a for a in articles if a.get('source') == source]
        
        return jsonify({
            'success': True,
            'content': articles,
            'total': len(articles)
        })
        
    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'content': []
        }), 500

@app.route('/api/content/statistics')
def api_content_statistics():
    """API: 获取内容统计"""
    try:
        content_storage = get_content_storage()
        if not content_storage:
            return jsonify({
                'success': False,
                'error': '内容存储系统不可用'
            }), 500
        
        stats = content_storage.get_content_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"获取内容统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/content/task/<task_id>')
def api_task_content(task_id):
    """API: 获取任务的内容"""
    try:
        content_storage = get_content_storage()
        if not content_storage:
            return jsonify({
                'success': False,
                'error': '内容存储系统不可用'
            }), 500
        
        articles = content_storage.get_articles_by_task(task_id)
        return jsonify({
            'success': True,
            'articles': articles,
            'count': len(articles)
        })
        
    except Exception as e:
        logger.error(f"获取任务内容失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'articles': []
        }), 500

@app.route('/api/content/article/<article_id>')
def api_article_detail(article_id):
    """API: 获取文章详情"""
    try:
        content_storage = get_content_storage()
        if not content_storage:
            return jsonify({
                'success': False,
                'error': '内容存储系统不可用'
            }), 500
        
        article = content_storage.get_article_by_id(article_id)
        if article:
            return jsonify({'success': True, 'article': article})
        else:
            return jsonify({'success': False, 'error': '文章不存在'}), 404
    except Exception as e:
        logger.error(f"获取文章详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/content/batch-process', methods=['POST'])
def api_batch_process():
    """API: 批量处理内容"""
    try:
        content_processor = get_content_processor()
        if not content_processor:
            return jsonify({
                'success': False,
                'error': '内容处理器不可用'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        process_type = data.get('type')
        content_ids = data.get('content_ids', [])
        params = {k: v for k, v in data.items() if k not in ['type', 'content_ids']}
        
        if not process_type:
            return jsonify({'success': False, 'error': '处理类型不能为空'}), 400
        
        if not content_ids:
            return jsonify({'success': False, 'error': '内容ID列表不能为空'}), 400
        
        # 创建批量处理任务
        task_id = content_processor.create_batch_task(content_ids, process_type, params)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'批量{process_type}任务已创建',
            'content_count': len(content_ids)
        })
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== WebSocket事件处理 ====================

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
        content_storage = get_content_storage()
        
        all_tasks = task_manager.get_recent_tasks() if task_manager else []
        content_stats = content_storage.get_content_statistics() if content_storage else {}
        
        stats = {
            'total_tasks': len(all_tasks),
            'running_tasks': len([t for t in all_tasks if t.get('status') == 'running']),
            'completed_tasks': len([t for t in all_tasks if t.get('status') == 'completed']),
            'failed_tasks': len([t for t in all_tasks if t.get('status') == 'failed']),
            'total_articles': content_stats.get('total_stats', {}).get('total_articles', 0),
            'timestamp': datetime.now().isoformat()
        }
        emit('system_status', stats)
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        emit('error', {'message': str(e)})

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found_error(error):
    try:
        return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"404错误处理失败: {e}")
        return '<h1>404 - 页面未找到</h1><a href="/">返回首页</a>', 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template('500.html'), 500
    except Exception as e:
        logger.error(f"500错误处理失败: {e}")
        return '<h1>500 - 服务器内部错误</h1><a href="/">返回首页</a>', 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    logger.info("==========================================")
    logger.info("视频自动化系统Web界面 - 完整版")
    logger.info("==========================================")
    logger.info("正在启动Web服务器...")
    logger.info("访问地址: http://localhost:5002")
    logger.info("内容管理: http://localhost:5002/content")
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