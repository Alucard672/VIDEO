#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置路由模块
提供配置管理的Web界面
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import logging
import json
import os

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
config_bp = Blueprint('config', __name__)

@config_bp.route('/config')
def config():
    """配置页面"""
    try:
        # 获取配置信息
        config_data = _get_config_data()
        
        return render_template('config.html', 
                             config=config_data,
                             title="系统配置")
    except Exception as e:
        logger.error(f"渲染配置页面失败: {e}")
        return render_template('error.html', 
                             error="配置页面加载失败",
                             message=str(e)), 500

@config_bp.route('/api/config', methods=['GET'])
def get_config():
    """获取配置API"""
    try:
        config_data = _get_config_data()
        return jsonify({
            'success': True,
            'data': config_data
        })
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/api/config', methods=['POST'])
def update_config():
    """更新配置API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '无效的请求数据'
            }), 400
        
        # 更新配置
        _update_config_data(data)
        
        return jsonify({
            'success': True,
            'message': '配置更新成功'
        })
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_config_data():
    """获取配置数据"""
    try:
        # 尝试从config_manager获取配置
        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
            # 使用get_config方法获取各个配置项
            config_data = {}
            config_keys = [
                'database.path', 'database.backup_enabled', 'database.backup_interval',
                'web.host', 'web.port', 'web.debug',
                'task_manager.max_workers', 'task_manager.queue_size',
                'content_fetch.timeout', 'content_fetch.retry_count', 'content_fetch.user_agent',
                'monitoring.enabled', 'monitoring.interval', 'monitoring.retention_days'
            ]
            
            for key in config_keys:
                try:
                    value = config_manager.get_config(key)
                    # 构建嵌套字典结构
                    keys = key.split('.')
                    current = config_data
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = value
                except:
                    pass
            
            return config_data
        except ImportError:
            pass
        
        # 尝试从config.py获取配置
        try:
            import config
            config_data = {}
            for attr in dir(config):
                if not attr.startswith('_'):
                    value = getattr(config, attr)
                    if not callable(value):
                        config_data[attr] = value
            return config_data
        except ImportError:
            pass
        
        # 默认配置
        return {
            'database': {
                'path': 'tasks.db',
                'backup_enabled': True,
                'backup_interval': 3600
            },
            'web': {
                'host': '0.0.0.0',
                'port': 5001,
                'debug': True
            },
            'task_manager': {
                'max_workers': 3,
                'queue_size': 100
            },
            'content_fetch': {
                'timeout': 30,
                'retry_count': 3,
                'user_agent': 'VideoAutoPipeline/1.0'
            },
            'monitoring': {
                'enabled': True,
                'interval': 60,
                'retention_days': 30
            }
        }
    except Exception as e:
        logger.error(f"获取配置数据失败: {e}")
        return {}

def _update_config_data(data):
    """更新配置数据"""
    try:
        # 尝试使用config_manager更新配置
        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
            for key, value in data.items():
                config_manager.set_config(key, value)
            return
        except ImportError:
            pass
        
        # 如果没有config_manager，可以考虑写入配置文件
        # 这里暂时只记录日志
        logger.info(f"配置更新请求: {data}")
        
    except Exception as e:
        logger.error(f"更新配置数据失败: {e}")
        raise