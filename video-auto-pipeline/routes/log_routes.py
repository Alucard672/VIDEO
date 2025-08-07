from flask import Blueprint, render_template, request, jsonify
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 创建日志蓝图
log_bp = Blueprint('log', __name__)

@log_bp.route('/logs')
def logs():
    """日志查看页面"""
    try:
        # 获取日志数据
        logs_data = _get_logs_data()
        return render_template('logs.html', logs=logs_data)
    except Exception as e:
        logger.error(f"渲染日志页面失败: {e}")
        return render_template('error.html', error=str(e)), 500

@log_bp.route('/api/logs')
def api_logs():
    """获取日志数据API"""
    try:
        # 获取查询参数
        level = request.args.get('level', 'all')
        limit = int(request.args.get('limit', 100))
        search = request.args.get('search', '')
        
        logs_data = _get_logs_data(level=level, limit=limit, search=search)
        return jsonify({
            'success': True,
            'data': logs_data
        })
    except Exception as e:
        logger.error(f"获取日志数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@log_bp.route('/api/logs/download')
def api_download_logs():
    """下载日志文件"""
    try:
        from flask import send_file
        import tempfile
        import zipfile
        
        # 创建临时zip文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_file.name, 'w') as zipf:
            # 添加应用日志
            log_files = _find_log_files()
            for log_file in log_files:
                if os.path.exists(log_file):
                    zipf.write(log_file, os.path.basename(log_file))
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"下载日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@log_bp.route('/api/logs/clear', methods=['POST'])
def api_clear_logs():
    """清空日志"""
    try:
        data = request.get_json()
        log_type = data.get('type', 'all') if data else 'all'
        
        cleared_files = []
        log_files = _find_log_files()
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    # 清空文件内容而不是删除文件
                    with open(log_file, 'w') as f:
                        f.write('')
                    cleared_files.append(os.path.basename(log_file))
                except Exception as e:
                    logger.warning(f"清空日志文件失败 {log_file}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'已清空 {len(cleared_files)} 个日志文件',
            'files': cleared_files
        })
        
    except Exception as e:
        logger.error(f"清空日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_logs_data(level='all', limit=100, search=''):
    """获取日志数据"""
    try:
        logs = []
        log_files = _find_log_files()
        
        # 读取日志文件
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    # 解析日志行
                    for line in reversed(lines[-limit:]):  # 获取最新的日志
                        line = line.strip()
                        if not line:
                            continue
                            
                        # 简单的日志解析
                        log_entry = _parse_log_line(line, os.path.basename(log_file))
                        
                        # 过滤级别
                        if level != 'all' and log_entry['level'].lower() != level.lower():
                            continue
                            
                        # 搜索过滤
                        if search and search.lower() not in log_entry['message'].lower():
                            continue
                            
                        logs.append(log_entry)
                        
                except Exception as e:
                    logger.warning(f"读取日志文件失败 {log_file}: {e}")
        
        # 按时间排序
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 统计信息
        stats = {
            'total_logs': len(logs),
            'error_count': len([l for l in logs if l['level'].upper() == 'ERROR']),
            'warning_count': len([l for l in logs if l['level'].upper() == 'WARNING']),
            'info_count': len([l for l in logs if l['level'].upper() == 'INFO']),
            'debug_count': len([l for l in logs if l['level'].upper() == 'DEBUG'])
        }
        
        return {
            'logs': logs[:limit],
            'stats': stats,
            'files': [os.path.basename(f) for f in log_files if os.path.exists(f)]
        }
        
    except Exception as e:
        logger.error(f"获取日志数据失败: {e}")
        return {
            'logs': [],
            'stats': {
                'total_logs': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'debug_count': 0
            },
            'files': []
        }

def _find_log_files():
    """查找日志文件"""
    log_files = []
    
    # 常见的日志文件位置
    possible_locations = [
        'app.log',
        'error.log',
        'access.log',
        'debug.log',
        'logs/app.log',
        'logs/error.log',
        'logs/access.log',
        '/tmp/app.log',
        '/var/log/app.log'
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            log_files.append(location)
    
    # 查找当前目录下的.log文件
    try:
        for file in os.listdir('.'):
            if file.endswith('.log'):
                log_files.append(file)
    except:
        pass
    
    return list(set(log_files))  # 去重

def _parse_log_line(line, filename):
    """解析日志行"""
    try:
        # 尝试解析标准格式的日志
        # 格式: 2025-08-07 20:41:08430 - werkzeug - INFO - message
        parts = line.split(' - ', 3)
        
        if len(parts) >= 4:
            timestamp_str = parts[0]
            module = parts[1]
            level = parts[2]
            message = parts[3]
            
            # 解析时间戳
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S%f')
            except:
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = datetime.now()
            
            return {
                'timestamp': timestamp.isoformat(),
                'level': level.strip(),
                'module': module.strip(),
                'message': message.strip(),
                'file': filename
            }
    except:
        pass
    
    # 如果解析失败，返回原始行
    return {
        'timestamp': datetime.now().isoformat(),
        'level': 'UNKNOWN',
        'module': 'unknown',
        'message': line,
        'file': filename
    }