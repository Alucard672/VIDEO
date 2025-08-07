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
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控系统路由
提供系统监控页面和API
"""

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
            'cpu_percent': psutil.cpu_percent(interval=0.1),  # 减少阻塞时间
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
        
        # 获取进程信息
        processes = []
        try:
            if system_monitor:
                processes = system_monitor.get_process_info()
            else:
                # 如果系统监控模块不可用，使用psutil直接获取
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'create_time']):
                    try:
                        proc_info = proc.info
                        cpu_percent = proc_info.get('cpu_percent', 0)
                        if cpu_percent is not None and cpu_percent > 0.5:  # 只返回CPU使用率大于0.5%的进程
                            # 计算运行时间
                            create_time = datetime.fromtimestamp(proc_info['create_time'])
                            running_time = datetime.now() - create_time
                            hours, remainder = divmod(running_time.seconds, 3600)
                            minutes, _ = divmod(remainder, 60)
                            running_time_str = f"{hours}小时{minutes}分"
                            
                            # 格式化内存使用
                            memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                            memory_str = f"{memory_mb:.0f} MB"
                            
                            # 状态转换
                            status_map = {
                                'running': '运行中',
                                'sleeping': '休眠',
                                'disk-sleep': '磁盘休眠',
                                'stopped': '已停止',
                                'tracing-stop': '跟踪停止',
                                'zombie': '僵尸',
                                'dead': '已终止',
                                'wake-kill': '唤醒终止',
                                'waking': '唤醒中'
                            }
                            status_text = status_map.get(proc_info['status'], proc_info['status'])
                            
                            processes.append({
                                'pid': proc_info['pid'],
                                'name': proc_info['name'],
                                'cpu_percent': proc_info['cpu_percent'],
                                'memory_info': memory_str,
                                'status': proc_info['status'],
                                'status_text': status_text,
                                'running_time': running_time_str
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                        continue
                
                # 按CPU使用率排序
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                processes = processes[:10]  # 只显示前10个进程
        except Exception as e:
            print(f"获取进程信息失败: {e}")
        
        return render_template('monitoring.html', metrics=metrics, processes=processes)
    except Exception as e:
        print(f"渲染监控页面失败: {e}")
        return render_template('error.html', error=str(e))

# 添加缓存机制
_metrics_cache = None
_metrics_cache_time = 0
_metrics_cache_ttl = 2  # 缓存有效期2秒

@monitoring_bp.route('/api/monitoring/current-metrics')
def get_current_metrics():
    """获取当前系统指标"""
    global _metrics_cache, _metrics_cache_time, _metrics_cache_ttl
    
    try:
        # 检查缓存是否有效
        current_time = time.time()
        if _metrics_cache and (current_time - _metrics_cache_time) < _metrics_cache_ttl:
            return jsonify(_metrics_cache)
        
        # 如果系统监控模块可用，直接使用其缓存的指标
        if system_monitor:
            current_metrics = system_monitor.get_current_metrics()
            metrics = {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_percent': current_metrics.memory_percent,
                'disk_percent': current_metrics.disk_percent,
                'network_sent': current_metrics.network_sent,
                'network_recv': current_metrics.network_recv,
                'process_count': current_metrics.process_count,
                'temperature': current_metrics.temperature,
                'timestamp': current_metrics.timestamp
            }
        else:
            # 基本系统指标 - 使用interval=0.1而不是1，减少阻塞时间
            metrics = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_sent': 0,
                'network_recv': 0,
                'process_count': len(psutil.pids()),
                'temperature': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # 更新缓存
        _metrics_cache = metrics
        _metrics_cache_time = current_time
        
        return jsonify(metrics)
    except Exception as e:
        # 如果出错但缓存存在，返回缓存的数据
        if _metrics_cache:
            return jsonify(_metrics_cache)
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
            # 添加额外信息
            for proc in processes:
                try:
                    # 添加内存信息
                    if 'memory_percent' in proc:
                        memory_mb = proc['memory_percent'] * psutil.virtual_memory().total / 100 / 1024 / 1024
                        proc['memory_info'] = f"{memory_mb:.0f} MB"
                    
                    # 添加状态文本
                    status_map = {
                        'running': '运行中',
                        'sleeping': '休眠',
                        'disk-sleep': '磁盘休眠',
                        'stopped': '已停止',
                        'tracing-stop': '跟踪停止',
                        'zombie': '僵尸',
                        'dead': '已终止',
                        'wake-kill': '唤醒终止',
                        'waking': '唤醒中'
                    }
                    proc['status_text'] = status_map.get(proc['status'], proc['status'])
                    
                    # 添加运行时间
                    try:
                        p = psutil.Process(proc['pid'])
                        create_time = datetime.fromtimestamp(p.create_time())
                        running_time = datetime.now() - create_time
                        hours, remainder = divmod(running_time.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        proc['running_time'] = f"{hours}小时{minutes}分"
                    except:
                        proc['running_time'] = "未知"
                except:
                    pass
            return jsonify(processes)
        else:
            # 如果系统监控模块不可用，使用psutil直接获取
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'create_time']):
                try:
                    proc_info = proc.info
                    cpu_percent = proc_info.get('cpu_percent', 0)
                    if cpu_percent is not None and cpu_percent > 0.5:  # 只返回CPU使用率大于0.5%的进程
                        # 计算运行时间
                        create_time = datetime.fromtimestamp(proc_info.get('create_time', 0))
                        running_time = datetime.now() - create_time
                        hours, remainder = divmod(running_time.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        running_time_str = f"{hours}小时{minutes}分"
                        
                        # 格式化内存使用
                        memory_mb = 0
                        if proc_info.get('memory_info'):
                            memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                        memory_str = f"{memory_mb:.0f} MB"
                        
                        # 状态转换
                        status_map = {
                            'running': '运行中',
                            'sleeping': '休眠',
                            'disk-sleep': '磁盘休眠',
                            'stopped': '已停止',
                            'tracing-stop': '跟踪停止',
                            'zombie': '僵尸',
                            'dead': '已终止',
                            'wake-kill': '唤醒终止',
                            'waking': '唤醒中'
                        }
                        status = proc_info.get('status', '')
                        status_text = status_map.get(status, status)
                        
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': cpu_percent,
                            'memory_info': memory_str,
                            'status': status,
                            'status_text': status_text,
                            'running_time': running_time_str
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
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

@monitoring_bp.route('/api/processes/<int:pid>/restart', methods=['POST'])
def restart_process(pid):
    """重启进程"""
    try:
        # 检查进程是否存在
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            # 记录操作日志
            logger.info(f"尝试重启进程: {process_name} (PID: {pid})")
            
            # 在实际生产环境中，这里应该有更复杂的逻辑来安全地重启进程
            # 这里我们只是模拟重启操作
            return jsonify({
                'success': True, 
                'message': f'进程 {process_name} (PID: {pid}) 重启操作已发送',
                'process': {
                    'pid': pid,
                    'name': process_name,
                    'status': 'restarting'
                }
            })
        except psutil.NoSuchProcess:
            return jsonify({'success': False, 'message': f'进程 {pid} 不存在'}), 404
        except psutil.AccessDenied:
            return jsonify({'success': False, 'message': f'没有权限操作进程 {pid}'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@monitoring_bp.route('/api/processes/<int:pid>/stop', methods=['POST'])
def stop_process(pid):
    """停止进程"""
    try:
        # 检查进程是否存在
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            # 记录操作日志
            logger.info(f"尝试停止进程: {process_name} (PID: {pid})")
            
            # 在实际生产环境中，这里应该有更复杂的逻辑来安全地停止进程
            # 这里我们只是模拟停止操作
            return jsonify({
                'success': True, 
                'message': f'进程 {process_name} (PID: {pid}) 停止操作已发送',
                'process': {
                    'pid': pid,
                    'name': process_name,
                    'status': 'stopping'
                }
            })
        except psutil.NoSuchProcess:
            return jsonify({'success': False, 'message': f'进程 {pid} 不存在'}), 404
        except psutil.AccessDenied:
            return jsonify({'success': False, 'message': f'没有权限操作进程 {pid}'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
