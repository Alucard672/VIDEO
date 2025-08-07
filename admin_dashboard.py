#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员仪表板
提供系统管理、监控、统计等功能的Web界面
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_socketio import SocketIO, emit
import threading
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from config import *
    from analytics.analytics import VideoAnalytics
    from monitoring.system_monitor import SystemMonitor
except ImportError as e:
    print(f"导入模块失败: {e}")
    # 创建模拟类以防止错误
    class VideoAnalytics:
        def get_platform_summary(self, platform, days=30):
            return {"platform": platform, "total_videos": 0}
        def get_trending_analysis(self, platform=None, days=7):
            return []
        def generate_daily_report(self, date=None):
            return {"date": date or datetime.now().strftime('%Y-%m-%d'), "summary": {}}
    
    class SystemMonitor:
        def get_system_summary(self):
            return {"monitoring_status": "未启动"}
        def start_monitoring(self, interval=60):
            pass
        def stop_monitoring(self):
            pass

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin_dashboard_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化组件
analytics = VideoAnalytics()
monitor = SystemMonitor()

# 全局状态
dashboard_status = {
    'system_running': False,
    'monitoring_active': False,
    'last_update': datetime.now().isoformat(),
    'active_tasks': [],
    'error_count': 0
}

@app.route('/')
def admin_index():
    """管理员首页"""
    return render_template('admin/index.html')

@app.route('/admin/overview')
def admin_overview():
    """系统概览"""
    # 获取系统摘要
    system_summary = monitor.get_system_summary()
    
    # 获取平台统计
    platform_stats = {}
    for platform in ['douyin', 'bilibili']:
        platform_stats[platform] = analytics.get_platform_summary(platform, 7)
    
    # 获取今日报告
    daily_report = analytics.generate_daily_report()
    
    return render_template('admin/overview.html', 
                         system_summary=system_summary,
                         platform_stats=platform_stats,
                         daily_report=daily_report)

@app.route('/admin/analytics')
def admin_analytics():
    """数据分析页面"""
    return render_template('admin/analytics.html')

@app.route('/admin/monitoring')
def admin_monitoring():
    """系统监控页面"""
    return render_template('admin/monitoring.html')

@app.route('/admin/tasks')
def admin_tasks():
    """任务管理页面"""
    return render_template('admin/tasks.html')

@app.route('/admin/settings')
def admin_settings():
    """系统设置页面"""
    return render_template('admin/settings.html')

# API路由
@app.route('/api/admin/system_status')
def api_system_status():
    """获取系统状态"""
    return jsonify(dashboard_status)

@app.route('/api/admin/platform_stats')
def api_platform_stats():
    """获取平台统计数据"""
    platform = request.args.get('platform', 'all')
    days = int(request.args.get('days', 30))
    
    if platform == 'all':
        stats = {}
        for p in ['douyin', 'bilibili']:
            stats[p] = analytics.get_platform_summary(p, days)
        return jsonify(stats)
    else:
        stats = analytics.get_platform_summary(platform, days)
        return jsonify(stats)

@app.route('/api/admin/trending_videos')
def api_trending_videos():
    """获取热门视频"""
    platform = request.args.get('platform')
    days = int(request.args.get('days', 7))
    
    trending = analytics.get_trending_analysis(platform, days)
    return jsonify(trending)

@app.route('/api/admin/system_metrics')
def api_system_metrics():
    """获取系统指标"""
    hours = int(request.args.get('hours', 24))
    metrics = monitor.get_historical_data(hours)
    return jsonify(metrics)

@app.route('/api/admin/start_monitoring', methods=['POST'])
def api_start_monitoring():
    """启动系统监控"""
    try:
        interval = request.json.get('interval', 60)
        monitor.start_monitoring(interval)
        dashboard_status['monitoring_active'] = True
        return jsonify({'success': True, 'message': '监控已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/stop_monitoring', methods=['POST'])
def api_stop_monitoring():
    """停止系统监控"""
    try:
        monitor.stop_monitoring()
        dashboard_status['monitoring_active'] = False
        return jsonify({'success': True, 'message': '监控已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def create_admin_templates():
    """创建管理员模板"""
    templates_dir = project_root / "templates" / "admin"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # 管理员基础模板
    admin_base = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}管理员仪表板{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.css" rel="stylesheet">
    <style>
        .admin-sidebar { 
            min-height: 100vh; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .admin-sidebar .nav-link {
            color: rgba(255,255,255,0.8);
            border-radius: 8px;
            margin: 2px 0;
            transition: all 0.3s;
        }
        .admin-sidebar .nav-link:hover,
        .admin-sidebar .nav-link.active {
            color: white;
            background-color: rgba(255,255,255,0.2);
        }
        .admin-content { 
            padding: 30px; 
            background-color: #f8f9fa;
            min-height: 100vh;
        }
        .metric-card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-online { background-color: #28a745; }
        .status-offline { background-color: #dc3545; }
        .status-warning { background-color: #ffc107; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- 管理员侧边栏 -->
            <div class="col-md-2 admin-sidebar p-3">
                <div class="text-center mb-4">
                    <h4><i class="bi bi-shield-check"></i> 管理中心</h4>
                    <small>视频自动化系统</small>
                </div>
                <nav class="nav flex-column">
                    <a class="nav-link" href="/admin/overview">
                        <i class="bi bi-speedometer2"></i> 系统概览
                    </a>
                    <a class="nav-link" href="/admin/analytics">
                        <i class="bi bi-graph-up"></i> 数据分析
                    </a>
                    <a class="nav-link" href="/admin/monitoring">
                        <i class="bi bi-activity"></i> 系统监控
                    </a>
                    <a class="nav-link" href="/admin/tasks">
                        <i class="bi bi-list-task"></i> 任务管理
                    </a>
                    <a class="nav-link" href="/admin/settings">
                        <i class="bi bi-gear"></i> 系统设置
                    </a>
                    <hr class="my-3">
                    <a class="nav-link" href="/">
                        <i class="bi bi-house"></i> 返回首页
                    </a>
                </nav>
                
                <div class="mt-auto pt-4">
                    <div class="card bg-transparent border-light">
                        <div class="card-body text-center">
                            <div class="status-indicator status-online"></div>
                            <small>系统运行中</small>
                            <div class="mt-2">
                                <small id="current-time"></small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 主内容区 -->
            <div class="col-md-10 admin-content">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script src="https://cdn.socket.io/4.0.1/socket.io.min.js"></script>
    
    <script>
        // 更新当前时间
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString('zh-CN');
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        // 高亮当前页面
        const currentPath = window.location.pathname;
        document.querySelectorAll('.admin-sidebar .nav-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    </script>
    
    {% block scripts %}{% endblock %}
</body>
</html>"""
    
    # 管理员首页模板
    admin_index = """{% extends "admin/base.html" %}
{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <h1 class="mb-0">
            <i class="bi bi-shield-check text-primary"></i> 
            管理员仪表板
        </h1>
        <p class="text-muted">视频自动化系统管理中心</p>
    </div>
</div>

<div class="row">
    <div class="col-md-3 mb-4">
        <div class="card metric-card text-center">
            <div class="card-body">
                <i class="bi bi-cpu display-4 text-primary mb-3"></i>
                <h5>系统状态</h5>
                <div class="metric-value text-success" id="system-status">运行中</div>
                <small class="text-muted">System Status</small>
            </div>
        </div>
    </div>
    
    <div class="col-md-3 mb-4">
        <div class="card metric-card text-center">
            <div class="card-body">
                <i class="bi bi-camera-video display-4 text-info mb-3"></i>
                <h5>今日视频</h5>
                <div class="metric-value text-info" id="daily-videos">0</div>
                <small class="text-muted">Videos Today</small>
            </div>
        </div>
    </div>
    
    <div class="col-md-3 mb-4">
        <div class="card metric-card text-center">
            <div class="card-body">
                <i class="bi bi-eye display-4 text-warning mb-3"></i>
                <h5>总观看量</h5>
                <div class="metric-value text-warning" id="total-views">0</div>
                <small class="text-muted">Total Views</small>
            </div>
        </div>
    </div>
    
    <div class="col-md-3 mb-4">
        <div class="card metric-card text-center">
            <div class="card-body">
                <i class="bi bi-exclamation-triangle display-4 text-danger mb-3"></i>
                <h5>系统告警</h5>
                <div class="metric-value text-danger" id="alert-count">0</div>
                <small class="text-muted">System Alerts</small>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-graph-up"></i> 系统性能趋势</h5>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-list-ul"></i> 快速操作</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="/admin/overview" class="btn btn-primary">
                        <i class="bi bi-speedometer2"></i> 系统概览
                    </a>
                    <a href="/admin/analytics" class="btn btn-info">
                        <i class="bi bi-graph-up"></i> 数据分析
                    </a>
                    <a href="/admin/monitoring" class="btn btn-warning">
                        <i class="bi bi-activity"></i> 系统监控
                    </a>
                    <a href="/admin/tasks" class="btn btn-success">
                        <i class="bi bi-list-task"></i> 任务管理
                    </a>
                </div>
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-header">
                <h5><i class="bi bi-info-circle"></i> 系统信息</h5>
            </div>
            <div class="card-body">
                <div id="system-info">
                    <p><strong>运行时间:</strong> <span id="uptime">计算中...</span></p>
                    <p><strong>CPU使用率:</strong> <span id="cpu-usage">0%</span></p>
                    <p><strong>内存使用率:</strong> <span id="memory-usage">0%</span></p>
                    <p><strong>磁盘使用率:</strong> <span id="disk-usage">0%</span></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// 初始化性能图表
const ctx = document.getElementById('performanceChart').getContext('2d');
const performanceChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'CPU使用率',
            data: [],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }, {
            label: '内存使用率',
            data: [],
            borderColor: 'rgb(255, 99, 132)',
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                max: 100
            }
        }
    }
});

// 加载数据
function loadDashboardData() {
    // 加载系统状态
    fetch('/api/admin/system_status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('system-status').textContent = 
                data.system_running ? '运行中' : '已停止';
        });
    
    // 加载平台统计
    fetch('/api/admin/platform_stats?days=1')
        .then(response => response.json())
        .then(data => {
            let totalVideos = 0;
            let totalViews = 0;
            
            Object.values(data).forEach(platform => {
                totalVideos += platform.total_videos || 0;
                totalViews += platform.total_views || 0;
            });
            
            document.getElementById('daily-videos').textContent = totalVideos;
            document.getElementById('total-views').textContent = totalViews.toLocaleString();
        });
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setInterval(loadDashboardData, 30000); // 每30秒更新一次
});
</script>
{% endblock %}"""
    
    # 系统概览模板
    admin_overview = """{% extends "admin/base.html" %}
{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <h1><i class="bi bi-speedometer2"></i> 系统概览</h1>
        <p class="text-muted">全面了解系统运行状态和关键指标</p>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-cpu"></i> 系统资源</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <div class="text-center">
                            <div class="metric-value text-primary">{{ system_summary.current_metrics.cpu_percent|round(1) }}%</div>
                            <small>CPU使用率</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="text-center">
                            <div class="metric-value text-info">{{ system_summary.current_metrics.memory_percent|round(1) }}%</div>
                            <small>内存使用率</small>
                        </div>
                    </div>
                </div>
                <hr>
                <div class="row">
                    <div class="col-6">
                        <div class="text-center">
                            <div class="metric-value text-warning">{{ system_summary.current_metrics.disk_percent|round(1) }}%</div>
                            <small>磁盘使用率</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="text-center">
                            <div class="metric-value text-success">{{ system_summary.current_metrics.process_count }}</div>
                            <small>进程数量</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-graph-up"></i> 平台统计</h5>
            </div>
            <div class="card-body">
                {% for platform, stats in platform_stats.items() %}
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span>{{ platform|title }}</span>
                    <div>
                        <span class="badge bg-primary">{{ stats.total_videos }} 视频</span>
                        <span class="badge bg-info">{{ stats.total_views }} 观看</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-calendar-day"></i> 今日报告</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3 text-center">
                        <div class="metric-value text-primary">{{ daily_report.summary.total_videos or 0 }}</div>
                        <small>今日发布视频</small>
                    </div>
                    <div class="col-md-3 text-center">
                        <div class="metric-value text-info">{{ daily_report.summary.total_views or 0 }}</div>
                        <small>今日总观看量</small>
                    </div>
                    <div class="col-md-3 text-center">
                        <div class="metric-value text-success">{{ daily_report.summary.total_likes or 0 }}</div>
                        <small>今日总点赞</small>
                    </div>
                    <div class="col-md-3 text-center">
                        <div class="metric-value text-warning">{{ daily_report.summary.total_comments or 0 }}</div>
                        <small>今日总评论</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""
    
    # 写入模板文件
    (templates_dir / "base.html").write_text(admin_base, encoding='utf-8')
    (templates_dir / "index.html").write_text(admin_index, encoding='utf-8')
    (templates_dir / "overview.html").write_text(admin_overview, encoding='utf-8')

if __name__ == '__main__':
    # 创建模板文件
    create_admin_templates()
    
    print("==========================================")
    print("管理员仪表板")
    print("==========================================")
    print("正在启动管理员Web服务器...")
    print("访问地址: http://localhost:5001")
    print("按 Ctrl+C 停止服务器")
    print("==========================================")
    
    # 启动Flask应用
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)