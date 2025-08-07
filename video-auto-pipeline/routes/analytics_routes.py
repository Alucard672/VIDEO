#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析路由模块
提供数据分析的Web界面
"""

from flask import Blueprint, render_template, request, jsonify
import logging
import json
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics():
    """分析页面"""
    try:
        # 获取分析数据
        analytics_data = _get_analytics_data()
        
        return render_template('analytics.html', 
                             analytics=analytics_data,
                             title="数据分析")
    except Exception as e:
        logger.error(f"渲染分析页面失败: {e}")
        return render_template('error.html', 
                             error="分析页面加载失败",
                             message=str(e)), 500

@analytics_bp.route('/api/analytics', methods=['GET'])
def get_analytics():
    """获取分析数据API"""
    try:
        analytics_data = _get_analytics_data()
        return jsonify({
            'success': True,
            'data': analytics_data
        })
    except Exception as e:
        logger.error(f"获取分析数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/tasks', methods=['GET'])
def get_task_analytics():
    """获取任务分析数据API"""
    try:
        task_analytics = _get_task_analytics()
        return jsonify({
            'success': True,
            'data': task_analytics
        })
    except Exception as e:
        logger.error(f"获取任务分析数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/content', methods=['GET'])
def get_content_analytics():
    """获取内容分析数据API"""
    try:
        content_analytics = _get_content_analytics()
        return jsonify({
            'success': True,
            'data': content_analytics
        })
    except Exception as e:
        logger.error(f"获取内容分析数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_analytics_data():
    """获取分析数据"""
    try:
        # 获取任务分析数据
        task_analytics = _get_task_analytics()
        
        # 获取内容分析数据
        content_analytics = _get_content_analytics()
        
        # 获取系统性能数据
        performance_data = _get_performance_data()
        
        return {
            'tasks': task_analytics,
            'content': content_analytics,
            'performance': performance_data,
            'summary': {
                'total_tasks': task_analytics.get('total', 0),
                'total_content': content_analytics.get('total', 0),
                'success_rate': task_analytics.get('success_rate', 0),
                'avg_processing_time': performance_data.get('avg_processing_time', 0)
            }
        }
    except Exception as e:
        logger.error(f"获取分析数据失败: {e}")
        return {}

def _get_task_analytics():
    """获取任务分析数据"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取任务统计
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count
            FROM tasks 
            GROUP BY status
        ''')
        status_stats = dict(cursor.fetchall())
        
        # 获取任务类型统计
        cursor.execute('''
            SELECT 
                task_type,
                COUNT(*) as count
            FROM tasks 
            GROUP BY task_type
        ''')
        type_stats = dict(cursor.fetchall())
        
        # 获取最近7天的任务创建趋势
        cursor.execute('''
            SELECT 
                DATE(created_time) as date,
                COUNT(*) as count
            FROM tasks 
            WHERE created_time >= datetime('now', '-7 days')
            GROUP BY DATE(created_time)
            ORDER BY date
        ''')
        daily_stats = dict(cursor.fetchall())
        
        conn.close()
        
        total_tasks = sum(status_stats.values())
        completed_tasks = status_stats.get('completed', 0)
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'total': total_tasks,
            'by_status': status_stats,
            'by_type': type_stats,
            'daily_trend': daily_stats,
            'success_rate': round(success_rate, 2)
        }
    except Exception as e:
        logger.error(f"获取任务分析数据失败: {e}")
        return {
            'total': 0,
            'by_status': {},
            'by_type': {},
            'daily_trend': {},
            'success_rate': 0
        }

def _get_content_analytics():
    """获取内容分析数据"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 尝试获取内容统计
        try:
            cursor.execute('''
                SELECT 
                    source_type,
                    COUNT(*) as count
                FROM content 
                GROUP BY source_type
            ''')
            source_stats = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM content')
            total_content = cursor.fetchone()[0]
        except:
            # 如果content表不存在，使用默认值
            source_stats = {}
            total_content = 0
        
        conn.close()
        
        return {
            'total': total_content,
            'by_source': source_stats,
            'quality_score': 85.5,  # 模拟数据
            'avg_length': 1250      # 模拟数据
        }
    except Exception as e:
        logger.error(f"获取内容分析数据失败: {e}")
        return {
            'total': 0,
            'by_source': {},
            'quality_score': 0,
            'avg_length': 0
        }

def _get_performance_data():
    """获取性能数据"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 计算平均处理时间
        cursor.execute('''
            SELECT 
                AVG(
                    CASE 
                        WHEN completed_time IS NOT NULL AND started_time IS NOT NULL 
                        THEN (julianday(completed_time) - julianday(started_time)) * 24 * 60 * 60
                        ELSE NULL 
                    END
                ) as avg_processing_time
            FROM tasks 
            WHERE status = 'completed'
        ''')
        result = cursor.fetchone()
        avg_processing_time = result[0] if result and result[0] else 0
        
        conn.close()
        
        return {
            'avg_processing_time': round(avg_processing_time, 2),
            'cpu_usage': 45.2,      # 模拟数据
            'memory_usage': 62.8,   # 模拟数据
            'disk_usage': 38.5      # 模拟数据
        }
    except Exception as e:
        logger.error(f"获取性能数据失败: {e}")
        return {
            'avg_processing_time': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0
        }