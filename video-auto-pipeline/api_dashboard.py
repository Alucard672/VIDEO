#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表板API端点
提供仪表板所需的统计数据和最近任务信息
"""

import logging
from flask import Blueprint, jsonify
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 创建蓝图
dashboard_api = Blueprint('dashboard_api', __name__)

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

def get_content_storage():
    try:
        from content_storage import content_storage
        return content_storage
    except Exception as e:
        logger.error(f"导入ContentStorage失败: {e}")
        return None

@dashboard_api.route('/api/dashboard/stats')
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/dashboard/recent-tasks')
def api_recent_tasks():
    """API: 获取最近的任务"""
    try:
        task_manager = get_task_manager()
        if not task_manager:
            return jsonify({
                'success': False,
                'error': '任务管理器不可用'
            }), 500
        
        # 获取最近的任务
        recent_tasks = task_manager.get_recent_tasks(limit=10)
        
        return jsonify({
            'success': True,
            'tasks': recent_tasks
        })
        
    except Exception as e:
        logger.error(f"获取最近任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/monitoring/current-metrics')
def api_current_metrics():
    """API: 获取当前系统指标"""
    try:
        import psutil
        
        # 获取系统指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count()
            },
            'memory': {
                'percent': memory.percent,
                'used': memory.used,
                'total': memory.total,
                'available': memory.available
            },
            'disk': {
                'percent': disk.percent,
                'used': disk.used,
                'total': disk.total,
                'free': disk.free
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except ImportError:
        # 如果psutil不可用，返回模拟数据
        metrics = {
            'cpu': {'percent': 0, 'cores': 4},
            'memory': {'percent': 0, 'used': 0, 'total': 8589934592, 'available': 8589934592},
            'disk': {'percent': 0, 'used': 0, 'total': 1000000000000, 'free': 1000000000000},
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/analytics/overview')
def api_analytics_overview():
    """API: 获取分析概览数据"""
    try:
        task_manager = get_task_manager()
        content_storage = get_content_storage()
        
        # 获取任务趋势数据（最近7天）
        task_trends = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            # 这里应该从数据库获取实际数据，暂时使用模拟数据
            task_trends.append({
                'date': date_str,
                'tasks': max(0, 10 - i * 2),
                'success_rate': max(0.5, 1.0 - i * 0.1)
            })
        
        # 获取内容统计
        content_stats = content_storage.get_content_statistics() if content_storage else {}
        
        return jsonify({
            'success': True,
            'analytics': {
                'task_trends': list(reversed(task_trends)),
                'content_stats': content_stats,
                'performance': {
                    'avg_task_duration': 120,  # 秒
                    'success_rate': 0.85,
                    'error_rate': 0.15
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取分析数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500