#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理路由
提供任务管理相关的API和页面路由
"""

import logging
from flask import Blueprint, render_template, request, jsonify, abort
from task_manager import TaskManager

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
task_bp = Blueprint('task', __name__)

# 获取任务管理器实例
task_manager = None

def init_task_manager(manager):
    """初始化任务管理器
    
    Args:
        manager: 任务管理器实例
    """
    global task_manager
    task_manager = manager

@task_bp.route('/tasks')
def tasks_page():
    """任务管理页面"""
    try:
        # 获取所有任务
        tasks = task_manager.get_all_tasks() if task_manager else []
        
        # 获取任务统计
        stats = task_manager.get_stats() if task_manager else {
            "total": 0,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        # 转换为前端需要的格式
        task_list = []
        for task in tasks:
            status_text = {
                "pending": "等待中",
                "running": "运行中",
                "completed": "已完成",
                "failed": "失败",
                "cancelled": "已取消"
            }.get(task["status"], "未知")
            
            task_list.append({
                "id": task["id"],
                "name": task["name"],
                "task_type": task["type"],
                "status": task["status"],
                "status_text": status_text,
                "progress": task["progress"],
                "priority": task.get("config", {}).get("priority", 2),
                "error_message": task["error"],
                "created_time": task["created_at"],
                "started_time": task.get("started_at"),
                "completed_time": task["completed_at"],
                "retry_count": task.get("config", {}).get("retry_count", 0),
                "max_retries": task.get("config", {}).get("max_retries", 3)
            })
        
        # 统计今日任务数
        today_tasks = len(tasks)
        running_tasks = stats["running"]
        completed_tasks = stats["completed"]
        failed_tasks = stats["failed"]
        
        stats_for_template = {
            "today_tasks": today_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks
        }
        
        return render_template('tasks.html', tasks=task_list, stats=stats_for_template)
    
    except Exception as e:
        logger.error(f"渲染任务页面失败: {e}")
        return render_template('error.html', error=str(e))

@task_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表API"""
    try:
        # 获取查询参数
        task_type = request.args.get('type')
        status = request.args.get('status')
        
        # 根据参数获取任务
        if task_type:
            tasks = task_manager.get_tasks_by_type(task_type)
        elif status:
            tasks = task_manager.get_tasks_by_status(status)
        else:
            tasks = task_manager.get_all_tasks()
        
        return jsonify({"success": True, "tasks": tasks})
    
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@task_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情API"""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            return jsonify({"success": False, "error": "任务不存在"}), 404
        
        return jsonify({"success": True, "task": task.to_dict()})
    
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@task_bp.route('/api/tasks', methods=['POST'])
def create_task():
    """创建任务API"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        task_name = data.get('name')
        task_type = data.get('task_type')
        config = data.get('params', {})
        
        if not task_name or not task_type:
            return jsonify({"success": False, "error": "任务名称和类型不能为空"}), 400
        
        # 添加优先级
        if 'priority' in data:
            config['priority'] = data['priority']
        
        # 创建任务
        task_id = task_manager.create_task(task_name, task_type, config)
        
        return jsonify({"success": True, "task_id": task_id})
    
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@task_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务API"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        task = task_manager.get_task(task_id)
        if not task:
            return jsonify({"success": False, "error": "任务不存在"}), 404
        
        # 更新任务状态
        if 'status' in data:
            status = data['status']
            if status == 'cancelled':
                task_manager.cancel_task(task_id)
            elif status == 'pending':
                # 重置任务状态为等待
                task.status = 'pending'
                if 'retry_count' in data:
                    task.config['retry_count'] = data['retry_count']
                task_manager.task_queue.put(task_id)
                task_manager._update_task_in_db(task)
        
        return jsonify({"success": True})
    
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@task_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务API"""
    try:
        result = task_manager.delete_task(task_id)
        if not result:
            return jsonify({"success": False, "error": "删除任务失败"}), 400
        
        return jsonify({"success": True})
    
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@task_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计API"""
    try:
        stats = task_manager.get_stats() if task_manager else {
            "total": 0,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        # 统计今日任务数
        today_tasks = stats["total"]
        running_tasks = stats["running"]
        completed_tasks = stats["completed"]
        failed_tasks = stats["failed"]
        
        return jsonify({
            "success": True,
            "today_tasks": today_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks
        })
    
    except Exception as e:
        logger.error(f"获取仪表盘统计失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500