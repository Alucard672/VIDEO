#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析页面路由
提供数据分析和报告功能
"""

import logging
from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 创建蓝图
analytics_bp = Blueprint('analytics', __name__)

def get_task_manager():
    try:
        from task_manager import TaskManager
        return TaskManager()
    except Exception as e:
        logger.error(f"导入TaskManager失败: {e}")
        return None

def get_content_storage():
    try:
        from content_storage import content_storage
        return content_storage
    except Exception as e:
        logger.error(f"导入ContentStorage失败: {e}")
        return None

@analytics_bp.route('/analytics')
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
        
        return render_template('analytics.html',
                             task_stats=task_stats,
                             content_stats=total_stats,
                             category_stats=category_stats,
                             source_stats=source_stats)
        
    except Exception as e:
        logger.error(f"渲染分析页面失败: {e}")
        return f"页面加载失败: {e}", 500

@analytics_bp.route('/reports')
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

@analytics_bp.route('/config')
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

@analytics_bp.route('/logs')
def logs_page():
    """日志页面"""
    try:
        # 读取日志文件
        log_entries = []
        try:
            with open('web_app.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-100:]  # 最近100行
                for line in lines:
                    if line.strip():
                        log_entries.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'level': 'INFO',
                            'message': line.strip()
                        })
        except FileNotFoundError:
            log_entries = [
                {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'INFO',
                    'message': '日志文件不存在或为空'
                }
            ]
        
        return render_template('logs.html', log_entries=log_entries)
        
    except Exception as e:
        logger.error(f"渲染日志页面失败: {e}")
        return f"页面加载失败: {e}", 500

@analytics_bp.route('/users')
def users_page():
    """用户管理页面"""
    try:
        from user_manager import UserManager
        user_manager = UserManager()
        
        users = user_manager.get_all_users()
        
        return render_template('users.html', users=users)
        
    except Exception as e:
        logger.error(f"渲染用户页面失败: {e}")
        return f"页面加载失败: {e}", 500