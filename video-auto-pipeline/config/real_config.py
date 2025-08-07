#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实环境配置系统
支持从环境变量、配置文件、数据库等多种方式读取配置
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RealConfig:
    """真实环境配置管理器"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.data_dir = self.config_dir.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir.parent / ".env"
        
        # 数据库路径
        self.db_path = self.data_dir / "config.db"
        
        # 初始化配置
        self._init_config()
    
    def _init_config(self):
        """初始化配置"""
        # 创建默认配置
        default_config = {
            "system": {
                "debug": True,
                "host": "0.0.0.0",
                "port": 8081,
                "secret_key": os.environ.get("SECRET_KEY", "your-secret-key-here"),
                "timezone": "Asia/Shanghai"
            },
            "database": {
                "type": "sqlite",
                "path": str(self.db_path),
                "backup_enabled": True,
                "backup_interval": 24  # 小时
            },
            "ai_services": {
                "openai": {
                    "api_key": os.environ.get("OPENAI_API_KEY", ""),
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                "fliki": {
                    "api_key": os.environ.get("FLIKI_API_KEY", ""),
                    "voice_id": "zh-CN-XiaoxiaoNeural",
                    "speed": 1.0
                },
                "heygen": {
                    "api_key": os.environ.get("HEYGEN_API_KEY", ""),
                    "model": "heygen-v1"
                }
            },
            "platforms": {
                "bilibili": {
                    "enabled": True,
                    "api_key": os.environ.get("BILIBILI_API_KEY", ""),
                    "cookie": os.environ.get("BILIBILI_COOKIE", "")
                },
                "douyin": {
                    "enabled": True,
                    "api_key": os.environ.get("DOUYIN_API_KEY", ""),
                    "cookie": os.environ.get("DOUYIN_COOKIE", "")
                },
                "kuaishou": {
                    "enabled": True,
                    "api_key": os.environ.get("KUAISHOU_API_KEY", ""),
                    "cookie": os.environ.get("KUAISHOU_COOKIE", "")
                },
                "xiaohongshu": {
                    "enabled": True,
                    "api_key": os.environ.get("XIAOHONGSHU_API_KEY", ""),
                    "cookie": os.environ.get("XIAOHONGSHU_COOKIE", "")
                },
                "youtube": {
                    "enabled": True,
                    "api_key": os.environ.get("YOUTUBE_API_KEY", ""),
                    "client_secret": os.environ.get("YOUTUBE_CLIENT_SECRET", "")
                }
            },
            "news_sources": {
                "sina": {
                    "enabled": True,
                    "api_url": "https://top.sina.com.cn/ws/GetTopDataList.php",
                    "categories": ["热点", "科技", "娱乐", "体育", "财经"]
                },
                "sohu": {
                    "enabled": True,
                    "api_url": "https://www.sohu.com/c/",
                    "categories": ["热点", "科技", "娱乐", "体育", "财经"]
                },
                "163": {
                    "enabled": True,
                    "api_url": "https://3g.163.com/touch/reconstruct/article/list/",
                    "categories": ["热点", "科技", "娱乐", "体育", "财经"]
                },
                "baidu": {
                    "enabled": True,
                    "api_url": "https://top.baidu.com/api/board",
                    "categories": ["热点"]
                }
            },
            "video_sources": {
                "bilibili": {
                    "enabled": True,
                    "api_url": "https://api.bilibili.com/x/web-interface/popular",
                    "categories": ["热门", "最新", "动画", "游戏", "音乐"]
                },
                "douyin": {
                    "enabled": True,
                    "api_url": "https://www.douyin.com/aweme/v1/web/hotsearch/billboard/word/",
                    "categories": ["热门", "最新", "娱乐", "生活", "美食"]
                },
                "kuaishou": {
                    "enabled": True,
                    "api_url": "https://www.kuaishou.com/graphql",
                    "categories": ["热门", "最新", "娱乐", "生活", "美食"]
                }
            },
            "storage": {
                "local": {
                    "enabled": True,
                    "path": str(self.data_dir / "uploads"),
                    "max_size": "10GB"
                },
                "tencent": {
                    "enabled": False,
                    "secret_id": os.environ.get("TENCENT_SECRET_ID", ""),
                    "secret_key": os.environ.get("TENCENT_SECRET_KEY", ""),
                    "region": "ap-beijing",
                    "bucket": "video-pipeline"
                }
            },
            "scheduler": {
                "enabled": True,
                "max_concurrent_tasks": 5,
                "task_timeout": 3600,  # 秒
                "retry_times": 3,
                "retry_delay": 300  # 秒
            },
            "monitoring": {
                "enabled": True,
                "log_level": "INFO",
                "log_file": str(self.data_dir.parent / "logs" / "system.log"),
                "metrics_enabled": True,
                "alert_enabled": True
            }
        }
        
        # 保存默认配置
        self._save_config(default_config)
        
        # 初始化数据库
        self._init_database()
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"配置已从文件加载: {self.config_file}")
                return config
            else:
                logger.warning("配置文件不存在，使用默认配置")
                return {}
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    
    def _init_database(self):
        """初始化配置数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建平台账户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    api_key TEXT,
                    api_secret TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    cookie TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    result TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"数据库已初始化: {self.db_path}")
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        # 首先从环境变量获取
        env_value = os.environ.get(key.upper())
        if env_value is not None:
            return env_value
        
        # 从配置文件获取
        config = self._load_config()
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, category: str = "system"):
        """设置配置值"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, category, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (key, json.dumps(value), category, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            logger.info(f"配置已更新: {key} = {value}")
            
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """获取平台配置"""
        config = self._load_config()
        return config.get("platforms", {}).get(platform, {})
    
    def get_news_source_config(self, source: str) -> Dict[str, Any]:
        """获取新闻源配置"""
        config = self._load_config()
        return config.get("news_sources", {}).get(source, {})
    
    def get_video_source_config(self, source: str) -> Dict[str, Any]:
        """获取视频源配置"""
        config = self._load_config()
        return config.get("video_sources", {}).get(source, {})
    
    def get_ai_config(self, service: str) -> Dict[str, Any]:
        """获取AI服务配置"""
        config = self._load_config()
        return config.get("ai_services", {}).get(service, {})
    
    def is_enabled(self, service: str) -> bool:
        """检查服务是否启用"""
        config = self._load_config()
        
        if service in config.get("platforms", {}):
            return config["platforms"][service].get("enabled", False)
        elif service in config.get("news_sources", {}):
            return config["news_sources"][service].get("enabled", False)
        elif service in config.get("video_sources", {}):
            return config["video_sources"][service].get("enabled", False)
        else:
            return False
    
    def get_database_path(self) -> str:
        """获取数据库路径"""
        return str(self.db_path)
    
    def get_upload_path(self) -> str:
        """获取上传路径"""
        config = self._load_config()
        storage_config = config.get("storage", {}).get("local", {})
        return storage_config.get("path", str(self.data_dir / "uploads"))
    
    def get_log_path(self) -> str:
        """获取日志路径"""
        config = self._load_config()
        monitoring_config = config.get("monitoring", {})
        return monitoring_config.get("log_file", str(self.data_dir.parent / "logs" / "system.log"))

# 全局配置实例
config = RealConfig()

def get_config() -> RealConfig:
    """获取配置实例"""
    return config 