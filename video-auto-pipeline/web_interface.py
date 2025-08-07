#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化系统Web界面
提供图形化的操作界面
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'video_auto_pipeline_secret_key'
socketio = SocketIO(app)

# 全局变量
system_status = {
    'is_running': False,
    'current_task': '',
    'progress': 0,
    'logs': [],
    'last_update': ''
}

class SystemManager:
    """系统管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_python = self.project_root / "venv" / "bin" / "python"
        if not self.venv_python.exists():
            self.venv_python = self.project_root / "venv" / "Scripts" / "python.exe"
    
    def run_test(self):
        """运行系统测试"""
        try:
            test_script = self.project_root / "test_system.py"
            result = subprocess.run(
                [str(self.venv_python), str(test_script)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def get_system_info(self):
        """获取系统信息"""
        info = {
            'python_version': '',
            'venv_status': '未激活',
            'dependencies': [],
            'disk_space': '',
            'last_test': ''
        }
        
        # 检查Python版本
        try:
            result = subprocess.run([str(self.venv_python), '--version'], 
                                 capture_output=True, text=True)
            info['python_version'] = result.stdout.strip()
        except:
            info['python_version'] = '未知'
        
        # 检查虚拟环境状态
        if self.venv_python.exists():
            info['venv_status'] = '已激活'
        
        # 检查依赖包
        try:
            result = subprocess.run([str(self.venv_python), '-m', 'pip', 'list'], 
                                 capture_output=True, text=True)
            info['dependencies'] = result.stdout.split('\n')[2:-1]
        except:
            info['dependencies'] = []
        
        # 检查磁盘空间
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_root)
            info['disk_space'] = f"总空间: {total // (1024**3)}GB, 可用: {free // (1024**3)}GB"
        except:
            info['disk_space'] = '未知'
        
        return info

# 创建系统管理器实例
system_manager = SystemManager()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """仪表板"""
    system_info = system_manager.get_system_info()
    return render_template('dashboard.html', system_info=system_info)

@app.route('/test')
def test_page():
    """测试页面"""
    return render_template('test.html')

@app.route('/config')
def config_page():
    """配置页面"""
    return render_template('config.html')

@app.route('/logs')
def logs_page():
    """日志页面"""
    return render_template('logs.html')

@app.route('/api/run_test', methods=['POST'])
def api_run_test():
    """API: 运行测试"""
    global system_status
    
    if system_status['is_running']:
        return jsonify({'success': False, 'message': '系统正在运行中'})
    
    system_status['is_running'] = True
    system_status['current_task'] = '系统测试'
    system_status['progress'] = 0
    system_status['logs'] = []
    
    # 在后台线程中运行测试
    def run_test_thread():
        try:
            result = system_manager.run_test()
            system_status['progress'] = 100
            system_status['is_running'] = False
            system_status['current_task'] = ''
            system_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 发送结果到前端
            socketio.emit('test_complete', {
                'success': result['success'],
                'output': result['output'],
                'error': result['error']
            })
        except Exception as e:
            system_status['is_running'] = False
            system_status['current_task'] = ''
            socketio.emit('test_error', {'error': str(e)})
    
    thread = threading.Thread(target=run_test_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': '测试已开始'})

@app.route('/api/system_status')
def api_system_status():
    """API: 获取系统状态"""
    return jsonify(system_status)

@app.route('/api/system_info')
def api_system_info():
    """API: 获取系统信息"""
    return jsonify(system_manager.get_system_info())

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    emit('connected', {'message': '已连接到服务器'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端断开连接')

def create_templates():
    """创建HTML模板"""
    templates_dir = project_root / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # 创建基础模板
    base_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}视频自动化系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .sidebar { min-height: 100vh; background-color: #f8f9fa; }
        .main-content { padding: 20px; }
        .status-card { border-left: 4px solid #007bff; }
        .log-container { height: 400px; overflow-y: auto; background-color: #f8f9fa; }
        .progress-bar { height: 20px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- 侧边栏 -->
            <div class="col-md-2 sidebar p-3">
                <h4 class="mb-4"><i class="bi bi-cpu"></i> 视频自动化</h4>
                <nav class="nav flex-column">
                    <a class="nav-link" href="/"><i class="bi bi-house"></i> 首页</a>
                    <a class="nav-link" href="/dashboard"><i class="bi bi-speedometer2"></i> 仪表板</a>
                    <a class="nav-link" href="/test"><i class="bi bi-play-circle"></i> 系统测试</a>
                    <a class="nav-link" href="/config"><i class="bi bi-gear"></i> 配置</a>
                    <a class="nav-link" href="/logs"><i class="bi bi-journal-text"></i> 日志</a>
                </nav>
            </div>
            
            <!-- 主内容区 -->
            <div class="col-md-10 main-content">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.socket.io/4.0.1/socket.io.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>"""
    
    # 创建首页模板
    index_template = """{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4"><i class="bi bi-play-circle"></i> 视频自动化系统</h1>
        <p class="lead">欢迎使用视频自动化系统！这是一个全自动的视频内容生成和发布系统。</p>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-4">
        <div class="card status-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-cpu"></i> 系统状态</h5>
                <p class="card-text" id="system-status">检查中...</p>
                <button class="btn btn-primary" onclick="checkSystemStatus()">
                    <i class="bi bi-arrow-clockwise"></i> 刷新状态
                </button>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card status-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-gear"></i> 快速操作</h5>
                <div class="d-grid gap-2">
                    <a href="/test" class="btn btn-success">
                        <i class="bi bi-play-circle"></i> 运行测试
                    </a>
                    <a href="/dashboard" class="btn btn-info">
                        <i class="bi bi-speedometer2"></i> 查看仪表板
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card status-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-info-circle"></i> 系统信息</h5>
                <div id="system-info">
                    <p>加载中...</p>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-list-ul"></i> 功能模块</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="bi bi-download display-4 text-primary"></i>
                                <h6>内容采集</h6>
                                <small class="text-muted">新闻抓取、视频下载</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="bi bi-pencil-square display-4 text-success"></i>
                                <h6>脚本生成</h6>
                                <small class="text-muted">AI内容生成</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="bi bi-music-note display-4 text-warning"></i>
                                <h6>TTS合成</h6>
                                <small class="text-muted">语音合成</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="bi bi-camera-video display-4 text-danger"></i>
                                <h6>视频处理</h6>
                                <small class="text-muted">剪辑、字幕</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function checkSystemStatus() {
    fetch('/api/system_status')
        .then(response => response.json())
        .then(data => {
            const status = data.is_running ? '运行中' : '空闲';
            document.getElementById('system-status').textContent = status;
        });
}

function loadSystemInfo() {
    fetch('/api/system_info')
        .then(response => response.json())
        .then(data => {
            const infoHtml = `
                <p><strong>Python版本:</strong> ${data.python_version}</p>
                <p><strong>虚拟环境:</strong> ${data.venv_status}</p>
                <p><strong>磁盘空间:</strong> ${data.disk_space}</p>
            `;
            document.getElementById('system-info').innerHTML = infoHtml;
        });
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', function() {
    checkSystemStatus();
    loadSystemInfo();
});
</script>
{% endblock %}"""
    
    # 创建测试页面模板
    test_template = """{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4"><i class="bi bi-play-circle"></i> 系统测试</h1>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-list-check"></i> 测试控制</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <button id="run-test-btn" class="btn btn-primary" onclick="runTest()">
                        <i class="bi bi-play-circle"></i> 运行系统测试
                    </button>
                    <button class="btn btn-secondary" onclick="clearLogs()">
                        <i class="bi bi-trash"></i> 清空日志
                    </button>
                </div>
                
                <div class="progress mb-3" style="display: none;" id="progress-container">
                    <div class="progress-bar" role="progressbar" style="width: 0%" id="progress-bar"></div>
                </div>
                
                <div class="alert alert-info" id="status-alert" style="display: none;">
                    <i class="bi bi-info-circle"></i> <span id="status-message"></span>
                </div>
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-header">
                <h5><i class="bi bi-terminal"></i> 测试输出</h5>
            </div>
            <div class="card-body">
                <div class="log-container p-3" id="log-container">
                    <p class="text-muted">等待测试开始...</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-info-circle"></i> 测试说明</h5>
            </div>
            <div class="card-body">
                <h6>测试项目：</h6>
                <ul class="list-unstyled">
                    <li><i class="bi bi-check-circle text-success"></i> 目录结构</li>
                    <li><i class="bi bi-check-circle text-success"></i> 依赖包</li>
                    <li><i class="bi bi-check-circle text-success"></i> 配置文件</li>
                    <li><i class="bi bi-x-circle text-danger"></i> 内容采集</li>
                    <li><i class="bi bi-x-circle text-danger"></i> 脚本生成</li>
                    <li><i class="bi bi-x-circle text-danger"></i> TTS生成</li>
                    <li><i class="bi bi-x-circle text-danger"></i> 视频剪辑</li>
                    <li><i class="bi bi-x-circle text-danger"></i> 封面生成</li>
                    <li><i class="bi bi-x-circle text-danger"></i> 账号管理</li>
                    <li><i class="bi bi-x-circle text-danger"></i> 上传模块</li>
                </ul>
                <hr>
                <p class="text-muted small">
                    <i class="bi bi-info-circle"></i> 
                    标记为红色的项目是预期失败的，因为这些模块还在开发中。
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://cdn.socket.io/4.0.1/socket.io.min.js"></script>
<script>
let socket = io();

socket.on('connect', function() {
    console.log('已连接到服务器');
});

socket.on('test_complete', function(data) {
    const logContainer = document.getElementById('log-container');
    const output = data.output || '';
    const error = data.error || '';
    
    let logContent = '';
    if (output) {
        logContent += `<pre class="text-success">${output}</pre>`;
    }
    if (error) {
        logContent += `<pre class="text-danger">${error}</pre>`;
    }
    
    logContainer.innerHTML = logContent;
    
    // 隐藏进度条
    document.getElementById('progress-container').style.display = 'none';
    
    // 更新状态
    const statusAlert = document.getElementById('status-alert');
    const statusMessage = document.getElementById('status-message');
    
    if (data.success) {
        statusAlert.className = 'alert alert-success';
        statusMessage.innerHTML = '<i class="bi bi-check-circle"></i> 测试完成！';
    } else {
        statusAlert.className = 'alert alert-danger';
        statusMessage.innerHTML = '<i class="bi bi-x-circle"></i> 测试失败！';
    }
    statusAlert.style.display = 'block';
    
    // 启用按钮
    document.getElementById('run-test-btn').disabled = false;
});

socket.on('test_error', function(data) {
    const logContainer = document.getElementById('log-container');
    logContainer.innerHTML = `<pre class="text-danger">错误: ${data.error}</pre>`;
    
    document.getElementById('progress-container').style.display = 'none';
    document.getElementById('run-test-btn').disabled = false;
});

function runTest() {
    const button = document.getElementById('run-test-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const statusAlert = document.getElementById('status-alert');
    const logContainer = document.getElementById('log-container');
    
    // 禁用按钮
    button.disabled = true;
    
    // 显示进度条
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    
    // 隐藏状态提示
    statusAlert.style.display = 'none';
    
    // 清空日志
    logContainer.innerHTML = '<p class="text-muted">正在运行测试...</p>';
    
    // 模拟进度
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 90) progress = 90;
        progressBar.style.width = progress + '%';
    }, 500);
    
    // 发送测试请求
    fetch('/api/run_test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
        } else {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressBar.className = 'progress-bar bg-danger';
            
            statusAlert.className = 'alert alert-danger';
            document.getElementById('status-message').innerHTML = 
                '<i class="bi bi-x-circle"></i> ' + data.message;
            statusAlert.style.display = 'block';
            
            button.disabled = false;
        }
    })
    .catch(error => {
        clearInterval(progressInterval);
        console.error('Error:', error);
        button.disabled = false;
    });
}

function clearLogs() {
    document.getElementById('log-container').innerHTML = 
        '<p class="text-muted">日志已清空...</p>';
}
</script>
{% endblock %}"""
    
    # 创建仪表板模板
    dashboard_template = """{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4"><i class="bi bi-speedometer2"></i> 系统仪表板</h1>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-info-circle"></i> 系统信息</h5>
            </div>
            <div class="card-body">
                <div id="system-info-details">
                    <p>加载中...</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-list-check"></i> 模块状态</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-check-circle text-success me-2"></i>
                            <span>目录结构</span>
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-check-circle text-success me-2"></i>
                            <span>依赖包</span>
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-check-circle text-success me-2"></i>
                            <span>配置文件</span>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-x-circle text-danger me-2"></i>
                            <span>内容采集</span>
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-x-circle text-danger me-2"></i>
                            <span>脚本生成</span>
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-x-circle text-danger me-2"></i>
                            <span>TTS生成</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-gear"></i> 快速操作</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <a href="/test" class="btn btn-primary w-100">
                            <i class="bi bi-play-circle"></i><br>
                            运行测试
                        </a>
                    </div>
                    <div class="col-md-3 mb-3">
                        <a href="/config" class="btn btn-info w-100">
                            <i class="bi bi-gear"></i><br>
                            系统配置
                        </a>
                    </div>
                    <div class="col-md-3 mb-3">
                        <a href="/logs" class="btn btn-warning w-100">
                            <i class="bi bi-journal-text"></i><br>
                            查看日志
                        </a>
                    </div>
                    <div class="col-md-3 mb-3">
                        <button class="btn btn-success w-100" onclick="refreshDashboard()">
                            <i class="bi bi-arrow-clockwise"></i><br>
                            刷新状态
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function loadSystemInfo() {
    fetch('/api/system_info')
        .then(response => response.json())
        .then(data => {
            const infoHtml = `
                <p><strong>Python版本:</strong> ${data.python_version}</p>
                <p><strong>虚拟环境:</strong> ${data.venv_status}</p>
                <p><strong>磁盘空间:</strong> ${data.disk_space}</p>
                <p><strong>依赖包数量:</strong> ${data.dependencies.length}</p>
            `;
            document.getElementById('system-info-details').innerHTML = infoHtml;
        });
}

function refreshDashboard() {
    loadSystemInfo();
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', function() {
    loadSystemInfo();
});
</script>
{% endblock %}"""
    
    # 创建配置页面模板
    config_template = """{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4"><i class="bi bi-gear"></i> 系统配置</h1>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-file-text"></i> 环境配置</h5>
            </div>
            <div class="card-body">
                <form>
                    <div class="mb-3">
                        <label for="openai_key" class="form-label">OpenAI API密钥</label>
                        <input type="password" class="form-control" id="openai_key" placeholder="请输入您的OpenAI API密钥">
                    </div>
                    
                    <div class="mb-3">
                        <label for="bilibili_cookie" class="form-label">哔哩哔哩 Cookie</label>
                        <input type="password" class="form-control" id="bilibili_cookie" placeholder="请输入哔哩哔哩 Cookie">
                    </div>
                    
                    <div class="mb-3">
                        <label for="douyin_cookie" class="form-label">抖音 Cookie</label>
                        <input type="password" class="form-control" id="douyin_cookie" placeholder="请输入抖音 Cookie">
                    </div>
                    
                    <div class="mb-3">
                        <label for="publish_interval" class="form-label">发布间隔（秒）</label>
                        <input type="number" class="form-control" id="publish_interval" value="3600">
                    </div>
                    
                    <div class="mb-3">
                        <label for="max_daily_posts" class="form-label">每日最大发布数量</label>
                        <input type="number" class="form-control" id="max_daily_posts" value="10">
                    </div>
                    
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-save"></i> 保存配置
                    </button>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-info-circle"></i> 配置说明</h5>
            </div>
            <div class="card-body">
                <h6>必需配置：</h6>
                <ul class="list-unstyled">
                    <li><i class="bi bi-check-circle text-success"></i> OpenAI API密钥</li>
                    <li><i class="bi bi-check-circle text-success"></i> 平台Cookie</li>
                </ul>
                
                <h6>可选配置：</h6>
                <ul class="list-unstyled">
                    <li><i class="bi bi-gear text-info"></i> 发布间隔</li>
                    <li><i class="bi bi-gear text-info"></i> 发布数量限制</li>
                </ul>
                
                <hr>
                <p class="text-muted small">
                    <i class="bi bi-exclamation-triangle"></i>
                    请妥善保管您的API密钥和Cookie信息，不要泄露给他人。
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""
    
    # 创建日志页面模板
    logs_template = """{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4"><i class="bi bi-journal-text"></i> 系统日志</h1>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5><i class="bi bi-list-ul"></i> 实时日志</h5>
                <div>
                    <button class="btn btn-sm btn-outline-secondary" onclick="clearLogs()">
                        <i class="bi bi-trash"></i> 清空
                    </button>
                    <button class="btn btn-sm btn-outline-primary" onclick="refreshLogs()">
                        <i class="bi bi-arrow-clockwise"></i> 刷新
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="log-container p-3" id="logs-container">
                    <p class="text-muted">暂无日志...</p>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-info-circle"></i> 日志说明</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-info-circle text-info me-2"></i>
                            <span>信息日志</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-check-circle text-success me-2"></i>
                            <span>成功日志</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-exclamation-triangle text-warning me-2"></i>
                            <span>警告日志</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-x-circle text-danger me-2"></i>
                            <span>错误日志</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function clearLogs() {
    document.getElementById('logs-container').innerHTML = 
        '<p class="text-muted">日志已清空...</p>';
}

function refreshLogs() {
    // 这里可以添加刷新日志的逻辑
    console.log('刷新日志');
}

// 模拟实时日志更新
setInterval(() => {
    const logsContainer = document.getElementById('logs-container');
    const now = new Date().toLocaleTimeString();
    const logEntry = `<div class="mb-1"><small class="text-muted">[${now}]</small> <span class="text-info">系统运行正常</span></div>`;
    
    if (logsContainer.children.length > 50) {
        logsContainer.innerHTML = '';
    }
    
    logsContainer.insertAdjacentHTML('beforeend', logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}, 5000);
</script>
{% endblock %}"""
    
    # 写入模板文件
    (templates_dir / "base.html").write_text(base_template, encoding='utf-8')
    (templates_dir / "index.html").write_text(index_template, encoding='utf-8')
    (templates_dir / "test.html").write_text(test_template, encoding='utf-8')
    (templates_dir / "dashboard.html").write_text(dashboard_template, encoding='utf-8')
    (templates_dir / "config.html").write_text(config_template, encoding='utf-8')
    (templates_dir / "logs.html").write_text(logs_template, encoding='utf-8')

if __name__ == '__main__':
    # 创建模板文件
    create_templates()
    
    print("==========================================")
    print("视频自动化系统Web界面")
    print("==========================================")
    print("正在启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("==========================================")
    
    # 启动Flask应用
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 