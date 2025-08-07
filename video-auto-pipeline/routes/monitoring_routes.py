#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控系统路由
提供系统监控页面和API
"""

from flask import Blueprint, render_template, jsonify, request
import psutil
import time
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 尝试导入系统监控模块
try:
    from monitoring.system_monitor import SystemMonitor
    system_monitor = SystemMonitor()
except ImportError:
    system_monitor = None
    print("警告: 系统监控模块不可用")

# 创建蓝图
monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/monitoring')
def monitoring_page():
    """监控页面"""
    try:
        # 获取当前系统指标
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
        
        # 如果系统监控模块可用，获取更多指标
        if system_monitor:
            current_metrics = system_monitor.get_current_metrics()
            metrics.update({
                'network_sent': current_metrics.network_sent,
                'network_recv': current_metrics.network_recv,
                'process_count': current_metrics.process_count,
                'temperature': current_metrics.temperature
            })
        
        return render_template('monitoring.html', metrics=metrics)
    except Exception as e:
        print(f"渲染监控页面失败: {e}")
        return render_template('error.html', error=str(e))

@monitoring_bp.route('/api/monitoring/current-metrics')
def get_current_metrics():
    """获取当前系统指标"""
    try:
        # 基本系统指标
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
        
        # 如果系统监控模块可用，获取更多指标
        if system_monitor:
            current_metrics = system_monitor.get_current_metrics()
            metrics.update({
                'network_sent': current_metrics.network_sent,
                'network_recv': current_metrics.network_recv,
                'process_count': current_metrics.process_count,
                'temperature': current_metrics.temperature
            })
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/historical-data')
def get_historical_data():
    """获取历史监控数据"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if system_monitor:
            data = system_monitor.get_historical_data(hours=hours)
            return jsonify(data)
        else:
            return jsonify([]), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/alerts')
def get_alerts():
    """获取系统告警"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if system_monitor:
            alerts = system_monitor.get_recent_alerts(hours=hours)
            return jsonify(alerts)
        else:
            return jsonify([]), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/processes')
def get_processes():
    """获取进程信息"""
    try:
        if system_monitor:
            processes = system_monitor.get_process_info()
            return jsonify(processes)
        else:
            # 如果系统监控模块不可用，使用psutil直接获取
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0.5:  # 只返回CPU使用率大于0.5%的进程
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent'],
                            'status': proc_info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return jsonify(processes[:20])  # 返回前20个进程
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/summary')
def get_system_summary():
    """获取系统摘要"""
    try:
        if system_monitor:
            summary = system_monitor.get_system_summary()
            return jsonify(summary)
        else:
            # 如果系统监控模块不可用，使用psutil直接获取
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 系统负载评估
            load_level = "正常"
            if cpu_percent > 80 or memory.percent > 85:
                load_level = "高负载"
            elif cpu_percent > 60 or memory.percent > 70:
                load_level = "中等负载"
            
            summary = {
                "current_metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "network_sent": 0,
                    "network_recv": 0,
                    "process_count": len(psutil.pids()),
                    "temperature": 0
                },
                "load_level": load_level,
                "monitoring_status": "未启动",
                "last_update": datetime.now().isoformat()
            }
            
            return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """开始系统监控"""
    try:
        if system_monitor:
            interval = request.json.get('interval', 60)
            system_monitor.start_monitoring(interval=interval)
            return jsonify({'success': True, 'message': '系统监控已启动'})
        else:
            return jsonify({'success': False, 'message': '系统监控模块不可用'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """停止系统监控"""
    try:
        if system_monitor:
            system_monitor.stop_monitoring()
            return jsonify({'success': True, 'message': '系统监控已停止'})
        else:
            return jsonify({'success': False, 'message': '系统监控模块不可用'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500