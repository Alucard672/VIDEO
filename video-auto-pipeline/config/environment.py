#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置管理器
负责加载和管理所有环境变量配置
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
import json
import yaml
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        初始化环境配置
        
        Args:
            env_file: 环境配置文件路径，默认为项目根目录的.env文件
        """
        self.project_root = Path(__file__).parent.parent
        self.env_file = env_file or self.project_root / '.env'
        
        # 加载环境变量
        self._load_environment()
        
        # 验证必需的配置
        self._validate_required_configs()
    
    def _load_environment(self):
        """加载环境变量"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"已加载环境配置文件: {self.env_file}")
        else:
            logger.warning(f"环境配置文件不存在: {self.env_file}")
            self._create_default_env_file()
    
    def _create_default_env_file(self):
        """创建默认环境配置文件"""
        default_env_content = """# 视频搬运矩阵自动化系统环境配置
# 请根据实际情况修改以下配置

# 数据库配置
DATABASE_URL=sqlite:///data/video_pipeline.db

# AI服务配置（请填入您的API密钥）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# TTS服务配置
FLIKI_API_KEY=your_fliki_api_key_here
HEYGEN_API_KEY=your_heygen_api_key_here

# 腾讯云配置
TENCENT_SECRET_ID=your_secret_id_here
TENCENT_SECRET_KEY=your_secret_key_here
TENCENT_REGION=ap-beijing

# 系统配置
SECRET_KEY=your_secret_key_here_please_change_this
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=5000
"""
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(default_env_content)
        
        logger.info(f"已创建默认环境配置文件: {self.env_file}")
    
    def _validate_required_configs(self):
        """验证必需的配置项"""
        required_configs = [
            'SECRET_KEY',
            'DATABASE_URL'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not self.get(config):
                missing_configs.append(config)
        
        if missing_configs:
            logger.warning(f"缺少必需的配置项: {', '.join(missing_configs)}")
    
    def get(self, key: str, default: Any = None, cast_type: type = str) -> Any:
        """
        获取环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值
            cast_type: 类型转换
            
        Returns:
            环境变量值
        """
        value = os.getenv(key, default)
        
        if value is None:
            return default
        
        # 类型转换
        try:
            if cast_type == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif cast_type == int:
                return int(value)
            elif cast_type == float:
                return float(value)
            elif cast_type == list:
                return [item.strip() for item in str(value).split(',') if item.strip()]
            elif cast_type == dict:
                return json.loads(value) if isinstance(value, str) else value
            else:
                return cast_type(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"配置项 {key} 类型转换失败: {e}，使用默认值: {default}")
            return default
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'url': self.get('DATABASE_URL', 'sqlite:///data/video_pipeline.db'),
            'pool_size': self.get('DATABASE_POOL_SIZE', 10, int),
            'timeout': self.get('DATABASE_TIMEOUT', 30, int),
            'echo': self.get('DATABASE_ECHO', False, bool)
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI服务配置"""
        return {
            'openai': {
                'api_key': self.get('OPENAI_API_KEY', ''),
                'model': self.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                'max_tokens': self.get('OPENAI_MAX_TOKENS', 2000, int),
                'temperature': self.get('OPENAI_TEMPERATURE', 0.7, float)
            },
            'fliki': {
                'api_key': self.get('FLIKI_API_KEY', '')
            },
            'heygen': {
                'api_key': self.get('HEYGEN_API_KEY', '')
            },
            'azure_speech': {
                'key': self.get('AZURE_SPEECH_KEY', ''),
                'region': self.get('AZURE_SPEECH_REGION', 'eastus')
            }
        }
    
    def get_cloud_config(self) -> Dict[str, Any]:
        """获取云服务配置"""
        return {
            'tencent': {
                'secret_id': self.get('TENCENT_SECRET_ID', ''),
                'secret_key': self.get('TENCENT_SECRET_KEY', ''),
                'region': self.get('TENCENT_REGION', 'ap-beijing'),
                'cos_bucket': self.get('TENCENT_COS_BUCKET', ''),
                'cos_region': self.get('TENCENT_COS_REGION', 'ap-beijing')
            },
            'aliyun': {
                'access_key': self.get('ALIYUN_ACCESS_KEY', ''),
                'secret_key': self.get('ALIYUN_SECRET_KEY', ''),
                'oss_bucket': self.get('ALIYUN_OSS_BUCKET', ''),
                'oss_endpoint': self.get('ALIYUN_OSS_ENDPOINT', '')
            }
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return {
            'upload_folder': self.get('UPLOAD_FOLDER', './uploads'),
            'temp_folder': self.get('TEMP_FOLDER', './temp'),
            'max_content_length': self.get('MAX_CONTENT_LENGTH', 2147483648, int),
            'allowed_extensions': self.get('ALLOWED_EXTENSIONS', 'mp4,avi,mov,mkv,flv,wmv,mp3,wav,aac', list)
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return {
            'secret_key': self.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'jwt_secret_key': self.get('JWT_SECRET_KEY', 'dev-jwt-secret-key'),
            'session_timeout': self.get('SESSION_TIMEOUT', 3600, int)
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return {
            'debug': self.get('DEBUG', True, bool),
            'log_level': self.get('LOG_LEVEL', 'INFO'),
            'host': self.get('HOST', '0.0.0.0'),
            'port': self.get('PORT', 5000, int),
            'workers': self.get('WORKERS', 4, int)
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return {
            'url': self.get('REDIS_URL', 'redis://localhost:6379/0'),
            'password': self.get('REDIS_PASSWORD', '')
        }
    
    def get_mail_config(self) -> Dict[str, Any]:
        """获取邮件配置"""
        return {
            'server': self.get('MAIL_SERVER', 'smtp.gmail.com'),
            'port': self.get('MAIL_PORT', 587, int),
            'use_tls': self.get('MAIL_USE_TLS', True, bool),
            'username': self.get('MAIL_USERNAME', ''),
            'password': self.get('MAIL_PASSWORD', '')
        }
    
    def get_platform_config(self) -> Dict[str, Any]:
        """获取平台配置"""
        return {
            'douyin': {
                'upload_interval': self.get('DOUYIN_UPLOAD_INTERVAL', 300, int),
                'max_daily_uploads': self.get('DOUYIN_MAX_DAILY_UPLOADS', 10, int)
            },
            'bilibili': {
                'upload_interval': self.get('BILIBILI_UPLOAD_INTERVAL', 600, int),
                'max_daily_uploads': self.get('BILIBILI_MAX_DAILY_UPLOADS', 5, int)
            },
            'xiaohongshu': {
                'upload_interval': self.get('XIAOHONGSHU_UPLOAD_INTERVAL', 900, int),
                'max_daily_uploads': self.get('XIAOHONGSHU_MAX_DAILY_UPLOADS', 3, int)
            },
            'kuaishou': {
                'upload_interval': self.get('KUAISHOU_UPLOAD_INTERVAL', 450, int),
                'max_daily_uploads': self.get('KUAISHOU_MAX_DAILY_UPLOADS', 8, int)
            },
            'youtube': {
                'api_key': self.get('YOUTUBE_API_KEY', ''),
                'upload_interval': self.get('YOUTUBE_UPLOAD_INTERVAL', 1800, int),
                'max_daily_uploads': self.get('YOUTUBE_MAX_DAILY_UPLOADS', 2, int)
            }
        }
    
    def get_video_config(self) -> Dict[str, Any]:
        """获取视频处理配置"""
        return {
            'output_resolution': self.get('VIDEO_OUTPUT_RESOLUTION', '1920x1080'),
            'output_fps': self.get('VIDEO_OUTPUT_FPS', 30, int),
            'output_bitrate': self.get('VIDEO_OUTPUT_BITRATE', '5000k'),
            'audio_bitrate': self.get('AUDIO_OUTPUT_BITRATE', '128k'),
            'audio_sample_rate': self.get('AUDIO_SAMPLE_RATE', 44100, int)
        }
    
    def get_content_review_config(self) -> Dict[str, Any]:
        """获取内容审核配置"""
        return {
            'enabled': self.get('CONTENT_REVIEW_ENABLED', True, bool),
            'sensitive_words_threshold': self.get('SENSITIVE_WORDS_THRESHOLD', 0.7, float),
            'auto_review_enabled': self.get('AUTO_REVIEW_ENABLED', True, bool)
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return {
            'enabled': self.get('MONITORING_ENABLED', True, bool),
            'metrics_retention_days': self.get('METRICS_RETENTION_DAYS', 30, int),
            'alert_email_enabled': self.get('ALERT_EMAIL_ENABLED', False, bool),
            'alert_webhook_url': self.get('ALERT_WEBHOOK_URL', '')
        }
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取任务调度配置"""
        return {
            'enabled': self.get('SCHEDULER_ENABLED', True, bool),
            'max_concurrent_tasks': self.get('MAX_CONCURRENT_TASKS', 5, int),
            'task_timeout': self.get('TASK_TIMEOUT', 3600, int),
            'retry_attempts': self.get('RETRY_ATTEMPTS', 3, int)
        }
    
    def get_analytics_config(self) -> Dict[str, Any]:
        """获取数据分析配置"""
        return {
            'enabled': self.get('ANALYTICS_ENABLED', True, bool),
            'retention_days': self.get('ANALYTICS_RETENTION_DAYS', 90, int),
            'export_format': self.get('EXPORT_FORMAT', 'json')
        }
    
    def get_backup_config(self) -> Dict[str, Any]:
        """获取备份配置"""
        return {
            'enabled': self.get('BACKUP_ENABLED', True, bool),
            'interval': self.get('BACKUP_INTERVAL', 86400, int),
            'retention_days': self.get('BACKUP_RETENTION_DAYS', 7, int),
            'location': self.get('BACKUP_LOCATION', './backups')
        }
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'database': self.get_database_config(),
            'ai': self.get_ai_config(),
            'cloud': self.get_cloud_config(),
            'storage': self.get_storage_config(),
            'security': self.get_security_config(),
            'system': self.get_system_config(),
            'redis': self.get_redis_config(),
            'mail': self.get_mail_config(),
            'platforms': self.get_platform_config(),
            'video': self.get_video_config(),
            'content_review': self.get_content_review_config(),
            'monitoring': self.get_monitoring_config(),
            'scheduler': self.get_scheduler_config(),
            'analytics': self.get_analytics_config(),
            'backup': self.get_backup_config()
        }
    
    def export_config(self, format_type: str = 'json', include_sensitive: bool = False) -> str:
        """
        导出配置
        
        Args:
            format_type: 导出格式 (json, yaml)
            include_sensitive: 是否包含敏感信息
            
        Returns:
            导出的配置字符串
        """
        config = self.get_all_configs()
        
        # 如果不包含敏感信息，则过滤掉
        if not include_sensitive:
            sensitive_keys = [
                'secret_key', 'jwt_secret_key', 'api_key', 'password',
                'secret_id', 'secret_key', 'access_key'
            ]
            config = self._filter_sensitive_data(config, sensitive_keys)
        
        if format_type.lower() == 'yaml':
            return yaml.dump(config, default_flow_style=False, allow_unicode=True)
        else:
            return json.dumps(config, indent=2, ensure_ascii=False)
    
    def _filter_sensitive_data(self, data: Any, sensitive_keys: List[str]) -> Any:
        """过滤敏感数据"""
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    filtered[key] = '***' if value else ''
                else:
                    filtered[key] = self._filter_sensitive_data(value, sensitive_keys)
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item, sensitive_keys) for item in data]
        else:
            return data
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置
        
        Returns:
            验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 验证数据库配置
        db_config = self.get_database_config()
        if not db_config['url']:
            validation_result['errors'].append('数据库URL未配置')
            validation_result['valid'] = False
        
        # 验证安全配置
        security_config = self.get_security_config()
        if security_config['secret_key'] in ['dev-secret-key-change-in-production', 'your_secret_key_here']:
            validation_result['warnings'].append('请更改默认的SECRET_KEY')
        
        # 验证AI服务配置
        ai_config = self.get_ai_config()
        if not ai_config['openai']['api_key']:
            validation_result['warnings'].append('OpenAI API密钥未配置，AI功能将不可用')
        
        # 验证云服务配置
        cloud_config = self.get_cloud_config()
        if not cloud_config['tencent']['secret_id'] or not cloud_config['tencent']['secret_key']:
            validation_result['warnings'].append('腾讯云配置未完整，相关功能将不可用')
        
        return validation_result

# 全局环境配置实例
env_config = EnvironmentConfig()

def get_config() -> EnvironmentConfig:
    """获取全局环境配置实例"""
    return env_config

def main():
    """测试函数"""
    config = EnvironmentConfig()
    
    print("=== 环境配置测试 ===")
    print(f"数据库配置: {config.get_database_config()}")
    print(f"系统配置: {config.get_system_config()}")
    print(f"AI配置: {config.get_ai_config()}")
    
    # 验证配置
    validation = config.validate_config()
    print(f"配置验证结果: {validation}")
    
    # 导出配置
    exported_config = config.export_config('json', include_sensitive=False)
    print(f"导出配置长度: {len(exported_config)} 字符")

if __name__ == "__main__":
    main()