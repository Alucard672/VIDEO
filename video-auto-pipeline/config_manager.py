#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
提供系统配置的管理、备份和恢复功能
"""

import os
import json
import yaml
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
import configparser

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.backup_dir = Path("config/backups")
        self.db_path = Path("data/config.db")
        
        # 创建目录
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.db_path.parent.mkdir(exist_ok=True)
        
        self._init_database()
        self._init_default_configs()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                data_type TEXT DEFAULT 'string',
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )
        ''')
        
        # 创建配置历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT NOT NULL,
                changed_by TEXT DEFAULT 'system',
                change_reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("配置管理数据库初始化完成")
    
    def _init_default_configs(self):
        """初始化默认配置"""
        default_configs = {
            "system": {
                "debug_mode": {"value": "false", "type": "boolean", "desc": "调试模式"},
                "log_level": {"value": "INFO", "type": "string", "desc": "日志级别"},
                "max_workers": {"value": "4", "type": "integer", "desc": "最大工作线程数"},
                "data_retention_days": {"value": "30", "type": "integer", "desc": "数据保留天数"}
            },
            "content_fetch": {
                "fetch_interval": {"value": "3600", "type": "integer", "desc": "采集间隔(秒)"},
                "max_articles_per_fetch": {"value": "50", "type": "integer", "desc": "每次采集最大文章数"},
                "enable_auto_fetch": {"value": "true", "type": "boolean", "desc": "启用自动采集"}
            },
            "ai": {
                "openai_api_key": {"value": "", "type": "string", "desc": "OpenAI API密钥", "sensitive": True},
                "model_name": {"value": "gpt-3.5-turbo", "type": "string", "desc": "AI模型名称"},
                "max_tokens": {"value": "2000", "type": "integer", "desc": "最大token数"},
                "temperature": {"value": "0.7", "type": "float", "desc": "生成温度"}
            },
            "tts": {
                "voice_provider": {"value": "azure", "type": "string", "desc": "语音提供商"},
                "voice_name": {"value": "zh-CN-XiaoxiaoNeural", "type": "string", "desc": "语音名称"},
                "speech_rate": {"value": "1.0", "type": "float", "desc": "语音速度"},
                "audio_format": {"value": "mp3", "type": "string", "desc": "音频格式"}
            },
            "video": {
                "output_resolution": {"value": "1920x1080", "type": "string", "desc": "输出分辨率"},
                "video_bitrate": {"value": "5000", "type": "integer", "desc": "视频比特率"},
                "audio_bitrate": {"value": "128", "type": "integer", "desc": "音频比特率"},
                "fps": {"value": "30", "type": "integer", "desc": "帧率"}
            },
            "upload": {
                "auto_upload": {"value": "false", "type": "boolean", "desc": "自动上传"},
                "upload_platforms": {"value": "bilibili,douyin", "type": "string", "desc": "上传平台"},
                "max_upload_retries": {"value": "3", "type": "integer", "desc": "最大上传重试次数"}
            },
            "notification": {
                "enable_email": {"value": "false", "type": "boolean", "desc": "启用邮件通知"},
                "email_smtp_server": {"value": "", "type": "string", "desc": "SMTP服务器"},
                "email_username": {"value": "", "type": "string", "desc": "邮箱用户名"},
                "email_password": {"value": "", "type": "string", "desc": "邮箱密码", "sensitive": True},
                "enable_webhook": {"value": "false", "type": "boolean", "desc": "启用Webhook通知"},
                "webhook_url": {"value": "", "type": "string", "desc": "Webhook URL"}
            }
        }
        
        # 检查并添加缺失的配置
        for category, configs in default_configs.items():
            for key, config_info in configs.items():
                if not self.get_config(category, key):
                    self.set_config(
                        category=category,
                        key=key,
                        value=config_info["value"],
                        description=config_info["desc"],
                        data_type=config_info["type"],
                        is_sensitive=config_info.get("sensitive", False)
                    )
    
    def get_config(self, category: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT value, data_type FROM configs 
            WHERE category = ? AND key = ?
        ''', (category, key))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return default
        
        value, data_type = result
        
        # 根据数据类型转换值
        try:
            if data_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif data_type == "integer":
                return int(value)
            elif data_type == "float":
                return float(value)
            elif data_type == "json":
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            logger.warning(f"配置值转换失败: {category}.{key} = {value}")
            return default
    
    def set_config(self, category: str, key: str, value: Any, 
                   description: str = "", data_type: str = "string",
                   is_sensitive: bool = False, changed_by: str = "system",
                   change_reason: str = ""):
        """设置配置值"""
        # 获取旧值用于历史记录
        old_value = self.get_config(category, key)
        
        # 转换值为字符串
        if isinstance(value, (dict, list)):
            str_value = json.dumps(value, ensure_ascii=False)
            data_type = "json"
        elif isinstance(value, bool):
            str_value = str(value).lower()
            data_type = "boolean"
        elif isinstance(value, int):
            str_value = str(value)
            data_type = "integer"
        elif isinstance(value, float):
            str_value = str(value)
            data_type = "float"
        else:
            str_value = str(value)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 插入或更新配置
        cursor.execute('''
            INSERT OR REPLACE INTO configs 
            (category, key, value, description, data_type, is_sensitive, updated_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (category, key, str_value, description, data_type, is_sensitive, datetime.now()))
        
        # 记录历史
        if old_value != value:
            cursor.execute('''
                INSERT INTO config_history 
                (category, key, old_value, new_value, changed_by, change_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (category, key, str(old_value) if old_value else None, 
                  str_value, changed_by, change_reason))
        
        conn.commit()
        conn.close()
        
        logger.info(f"配置已更新: {category}.{key} = {str_value}")
    
    def get_category_configs(self, category: str) -> Dict[str, Any]:
        """获取分类下的所有配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, value, data_type, description, is_sensitive 
            FROM configs WHERE category = ?
            ORDER BY key
        ''', (category,))
        
        configs = {}
        for row in cursor.fetchall():
            key, value, data_type, description, is_sensitive = row
            
            # 敏感信息不返回实际值
            if is_sensitive:
                display_value = "***" if value else ""
            else:
                # 转换数据类型
                if data_type == "boolean":
                    display_value = value.lower() in ("true", "1", "yes", "on")
                elif data_type == "integer":
                    display_value = int(value) if value else 0
                elif data_type == "float":
                    display_value = float(value) if value else 0.0
                elif data_type == "json":
                    display_value = json.loads(value) if value else {}
                else:
                    display_value = value
            
            configs[key] = {
                "value": display_value,
                "type": data_type,
                "description": description,
                "is_sensitive": is_sensitive
            }
        
        conn.close()
        return configs
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT category FROM configs ORDER BY category
        ''')
        
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        all_configs = {}
        for category in categories:
            all_configs[category] = self.get_category_configs(category)
        
        return all_configs
    
    def delete_config(self, category: str, key: str, changed_by: str = "system"):
        """删除配置"""
        old_value = self.get_config(category, key)
        if old_value is None:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 删除配置
        cursor.execute('''
            DELETE FROM configs WHERE category = ? AND key = ?
        ''', (category, key))
        
        # 记录历史
        cursor.execute('''
            INSERT INTO config_history 
            (category, key, old_value, new_value, changed_by, change_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (category, key, str(old_value), "", changed_by, "配置删除"))
        
        conn.commit()
        conn.close()
        
        logger.info(f"配置已删除: {category}.{key}")
        return True
    
    def backup_configs(self, backup_name: str = None) -> str:
        """备份配置"""
        if not backup_name:
            backup_name = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        # 获取所有配置（包括敏感信息）
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, key, value, description, data_type, is_sensitive
            FROM configs ORDER BY category, key
        ''')
        
        backup_data = {
            "backup_time": datetime.now().isoformat(),
            "backup_name": backup_name,
            "configs": {}
        }
        
        for row in cursor.fetchall():
            category, key, value, description, data_type, is_sensitive = row
            
            if category not in backup_data["configs"]:
                backup_data["configs"][category] = {}
            
            backup_data["configs"][category][key] = {
                "value": value,
                "description": description,
                "data_type": data_type,
                "is_sensitive": is_sensitive
            }
        
        conn.close()
        
        # 保存备份文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"配置备份完成: {backup_file}")
        return str(backup_file)
    
    def restore_configs(self, backup_file: str, changed_by: str = "system") -> bool:
        """恢复配置"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"备份文件不存在: {backup_file}")
            return False
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            configs = backup_data.get("configs", {})
            
            for category, category_configs in configs.items():
                for key, config_info in category_configs.items():
                    self.set_config(
                        category=category,
                        key=key,
                        value=config_info["value"],
                        description=config_info.get("description", ""),
                        data_type=config_info.get("data_type", "string"),
                        is_sensitive=config_info.get("is_sensitive", False),
                        changed_by=changed_by,
                        change_reason=f"从备份恢复: {backup_path.name}"
                    )
            
            logger.info(f"配置恢复完成: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"配置恢复失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.json"):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                backups.append({
                    "name": backup_data.get("backup_name", backup_file.stem),
                    "file": str(backup_file),
                    "backup_time": backup_data.get("backup_time", ""),
                    "size": backup_file.stat().st_size,
                    "config_count": sum(len(configs) for configs in backup_data.get("configs", {}).values())
                })
                
            except Exception as e:
                logger.warning(f"读取备份文件失败: {backup_file} - {e}")
        
        # 按时间排序
        backups.sort(key=lambda x: x["backup_time"], reverse=True)
        return backups
    
    def get_config_history(self, category: str = None, key: str = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """获取配置变更历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT category, key, old_value, new_value, changed_by, 
                   change_reason, timestamp
            FROM config_history
        '''
        params = []
        conditions = []
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if key:
            conditions.append("key = ?")
            params.append(key)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "category": row[0],
                "key": row[1],
                "old_value": row[2],
                "new_value": row[3],
                "changed_by": row[4],
                "change_reason": row[5],
                "timestamp": row[6]
            })
        
        conn.close()
        return history
    
    def export_configs(self, export_format: str = "json", 
                      include_sensitive: bool = False) -> str:
        """导出配置"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format.lower() == "yaml":
            export_file = self.config_dir / f"config_export_{timestamp}.yaml"
        else:
            export_file = self.config_dir / f"config_export_{timestamp}.json"
        
        # 获取配置数据
        all_configs = {}
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, key, value, data_type, is_sensitive
            FROM configs ORDER BY category, key
        ''')
        
        for row in cursor.fetchall():
            category, key, value, data_type, is_sensitive = row
            
            # 跳过敏感信息（除非明确要求包含）
            if is_sensitive and not include_sensitive:
                continue
            
            if category not in all_configs:
                all_configs[category] = {}
            
            # 转换数据类型
            if data_type == "boolean":
                converted_value = value.lower() in ("true", "1", "yes", "on")
            elif data_type == "integer":
                converted_value = int(value) if value else 0
            elif data_type == "float":
                converted_value = float(value) if value else 0.0
            elif data_type == "json":
                converted_value = json.loads(value) if value else {}
            else:
                converted_value = value
            
            all_configs[category][key] = converted_value
        
        conn.close()
        
        # 保存文件
        if export_format.lower() == "yaml":
            with open(export_file, 'w', encoding='utf-8') as f:
                yaml.dump(all_configs, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        else:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(all_configs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"配置导出完成: {export_file}")
        return str(export_file)
    
    def validate_config(self, category: str, key: str, value: Any) -> tuple[bool, str]:
        """验证配置值"""
        # 基本验证规则
        validation_rules = {
            "system": {
                "max_workers": lambda x: 1 <= int(x) <= 20,
                "data_retention_days": lambda x: 1 <= int(x) <= 365,
                "log_level": lambda x: x.upper() in ["DEBUG", "INFO", "WARNING", "ERROR"]
            },
            "content_fetch": {
                "fetch_interval": lambda x: 60 <= int(x) <= 86400,
                "max_articles_per_fetch": lambda x: 1 <= int(x) <= 1000
            },
            "ai": {
                "max_tokens": lambda x: 1 <= int(x) <= 8000,
                "temperature": lambda x: 0.0 <= float(x) <= 2.0
            },
            "tts": {
                "speech_rate": lambda x: 0.5 <= float(x) <= 2.0
            },
            "video": {
                "fps": lambda x: 15 <= int(x) <= 60,
                "video_bitrate": lambda x: 500 <= int(x) <= 50000,
                "audio_bitrate": lambda x: 64 <= int(x) <= 320
            }
        }
        
        if category in validation_rules and key in validation_rules[category]:
            try:
                validator = validation_rules[category][key]
                if not validator(value):
                    return False, f"配置值 {value} 不符合验证规则"
            except (ValueError, TypeError) as e:
                return False, f"配置值类型错误: {e}"
        
        return True, "验证通过"
    
    def reset_to_defaults(self, category: str = None, changed_by: str = "system"):
        """重置为默认配置"""
        if category:
            # 重置指定分类
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM configs WHERE category = ?', (category,))
            conn.commit()
            conn.close()
            
            logger.info(f"已重置分类配置: {category}")
        else:
            # 重置所有配置
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM configs')
            conn.commit()
            conn.close()
            
            logger.info("已重置所有配置")
        
        # 重新初始化默认配置
        self._init_default_configs()

def main():
    """主函数"""
    config_manager = ConfigManager()
    
    # 测试配置操作
    print("=== 配置管理器测试 ===")
    
    # 获取配置
    debug_mode = config_manager.get_config("system", "debug_mode")
    print(f"调试模式: {debug_mode}")
    
    # 设置配置
    config_manager.set_config("system", "debug_mode", True, changed_by="test")
    debug_mode = config_manager.get_config("system", "debug_mode")
    print(f"调试模式(更新后): {debug_mode}")
    
    # 获取分类配置
    system_configs = config_manager.get_category_configs("system")
    print(f"系统配置: {system_configs}")
    
    # 备份配置
    backup_file = config_manager.backup_configs("test_backup")
    print(f"备份文件: {backup_file}")
    
    # 列出备份
    backups = config_manager.list_backups()
    print(f"备份列表: {len(backups)} 个备份")
    
    # 获取历史记录
    history = config_manager.get_config_history(limit=5)
    print(f"配置历史: {len(history)} 条记录")
    
    # 导出配置
    export_file = config_manager.export_configs("json")
    print(f"导出文件: {export_file}")
    
    print("配置管理器测试完成")

if __name__ == "__main__":
    main()