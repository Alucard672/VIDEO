# -*- coding: utf-8 -*-
"""
视频搬运矩阵自动化系统配置文件
基于环境配置的统一配置管理
"""

import os
from pathlib import Path

# 尝试导入环境配置，如果失败则使用默认配置
try:
    import sys
    config_dir = Path(__file__).parent / "config"
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    from environment import get_config
    env_config = get_config()
except ImportError as e:
    print(f"导入环境配置失败: {e}")
    # 如果环境配置不存在，创建默认配置
    class DefaultConfig:
        def get_ai_config(self):
            return {
                'openai': {'api_key': '', 'model': 'gpt-3.5-turbo', 'max_tokens': 2000, 'temperature': 0.7},
                'fliki': {'api_key': ''},
                'heygen': {'api_key': ''},
                'azure_speech': {'key': '', 'region': ''}
            }
        
        def get_cloud_config(self):
            return {
                'tencent': {'secret_id': '', 'secret_key': '', 'region': 'ap-beijing', 'cos_bucket': '', 'cos_region': ''},
                'aliyun': {'access_key': '', 'secret_key': '', 'oss_bucket': '', 'oss_endpoint': ''}
            }
        
        def get_platform_config(self):
            return {
                'youtube': {'api_key': '', 'upload_interval': 3600, 'max_daily_uploads': 10},
                'douyin': {'upload_interval': 3600, 'max_daily_uploads': 10},
                'bilibili': {'upload_interval': 3600, 'max_daily_uploads': 10},
                'xiaohongshu': {'upload_interval': 3600, 'max_daily_uploads': 10},
                'kuaishou': {'upload_interval': 3600, 'max_daily_uploads': 10}
            }
        
        def get_database_config(self):
            return {'url': 'sqlite:///data/video_pipeline.db', 'pool_size': 10, 'timeout': 30}
        
        def get_video_config(self):
            return {
                'output_resolution': '1080p',
                'output_fps': 30,
                'output_bitrate': '2M',
                'audio_sample_rate': 44100,
                'audio_bitrate': '128k'
            }
        
        def get_system_config(self):
            return {'log_level': 'INFO', 'debug': True, 'host': '0.0.0.0', 'port': 5000, 'workers': 1}
        
        def get_content_review_config(self):
            return {'sensitive_words_threshold': 0.8, 'auto_review_enabled': True, 'enabled': True}
        
        def get_storage_config(self):
            return {
                'upload_folder': 'uploads',
                'temp_folder': 'temp',
                'max_content_length': 16 * 1024 * 1024,
                'allowed_extensions': ['.mp4', '.avi', '.mov', '.mp3', '.wav']
            }
        
        def get_security_config(self):
            return {'secret_key': 'dev-secret-key', 'jwt_secret_key': 'jwt-secret', 'session_timeout': 3600}
        
        def get_monitoring_config(self):
            return {'enabled': True, 'metrics_retention_days': 30, 'alert_email_enabled': False, 'alert_webhook_url': ''}
        
        def get_scheduler_config(self):
            return {'enabled': True, 'max_concurrent_tasks': 5, 'task_timeout': 3600, 'retry_attempts': 3}
        
        def get_analytics_config(self):
            return {'enabled': True, 'retention_days': 90, 'export_format': 'json'}
        
        def get_backup_config(self):
            return {'enabled': True, 'interval': 86400, 'retention_days': 30, 'location': 'backups'}
    
    env_config = DefaultConfig()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据存储目录
DATA_DIR = PROJECT_ROOT / "data"
VIDEOS_DIR = DATA_DIR / "videos"
AUDIO_DIR = DATA_DIR / "audio"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
LOGS_DIR = PROJECT_ROOT / "logs"
TEMP_DIR = PROJECT_ROOT / "temp"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
BACKUPS_DIR = PROJECT_ROOT / "backups"

# 创建必要的目录
for dir_path in [DATA_DIR, VIDEOS_DIR, AUDIO_DIR, THUMBNAILS_DIR, LOGS_DIR, TEMP_DIR, UPLOADS_DIR, BACKUPS_DIR]:
    dir_path.mkdir(exist_ok=True)

# 数据库路径
DATABASE_PATH = PROJECT_ROOT / "data" / "video_pipeline.db"

# API配置类
class APIConfig:
    """API服务配置"""
    def __init__(self):
        ai_config = env_config.get_ai_config()
        cloud_config = env_config.get_cloud_config()
        platform_config = env_config.get_platform_config()
        
        # OpenAI配置
        self.OPENAI_API_KEY = ai_config['openai']['api_key']
        self.OPENAI_MODEL = ai_config['openai']['model']
        self.OPENAI_MAX_TOKENS = ai_config['openai']['max_tokens']
        self.OPENAI_TEMPERATURE = ai_config['openai']['temperature']
        
        # TTS配置
        self.FLIKI_API_KEY = ai_config['fliki']['api_key']
        self.HEYGEN_API_KEY = ai_config['heygen']['api_key']
        self.AZURE_SPEECH_KEY = ai_config['azure_speech']['key']
        self.AZURE_SPEECH_REGION = ai_config['azure_speech']['region']
        
        # 腾讯云配置
        self.TENCENT_SECRET_ID = cloud_config['tencent']['secret_id']
        self.TENCENT_SECRET_KEY = cloud_config['tencent']['secret_key']
        self.TENCENT_REGION = cloud_config['tencent']['region']
        self.TENCENT_COS_BUCKET = cloud_config['tencent']['cos_bucket']
        self.TENCENT_COS_REGION = cloud_config['tencent']['cos_region']
        
        # 阿里云配置
        self.ALIYUN_ACCESS_KEY = cloud_config['aliyun']['access_key']
        self.ALIYUN_SECRET_KEY = cloud_config['aliyun']['secret_key']
        self.ALIYUN_OSS_BUCKET = cloud_config['aliyun']['oss_bucket']
        self.ALIYUN_OSS_ENDPOINT = cloud_config['aliyun']['oss_endpoint']
        
        # YouTube配置
        self.YOUTUBE_API_KEY = platform_config['youtube']['api_key']

# 数据库配置类
class DatabaseConfig:
    """数据库配置"""
    def __init__(self):
        db_config = env_config.get_database_config()
        
        self.DATABASE_URL = db_config['url']
        self.DATABASE_PATH = PROJECT_ROOT / "data" / "video_pipeline.db"
        self.POOL_SIZE = db_config['pool_size']
        self.TIMEOUT = db_config['timeout']
        self.ECHO = db_config.get('echo', False)

# 视频处理配置类
class VideoConfig:
    """视频处理配置"""
    def __init__(self):
        video_config = env_config.get_video_config()
        
        # 视频质量设置
        self.TARGET_RESOLUTION = video_config['output_resolution']
        self.TARGET_FPS = video_config['output_fps']
        self.TARGET_BITRATE = video_config['output_bitrate']
        
        # 音频设置
        self.AUDIO_SAMPLE_RATE = video_config['audio_sample_rate']
        self.AUDIO_BITRATE = video_config['audio_bitrate']
        
        # 视频时长限制
        self.MIN_DURATION = 30  # 秒
        self.MAX_DURATION = 900  # 秒 (15分钟)

# 上传配置类
class UploadConfig:
    """上传配置"""
    def __init__(self):
        platform_config = env_config.get_platform_config()
        
        # 抖音配置
        self.DOUYIN_UPLOAD_INTERVAL = platform_config['douyin']['upload_interval']
        self.DOUYIN_MAX_DAILY_UPLOADS = platform_config['douyin']['max_daily_uploads']
        
        # B站配置
        self.BILIBILI_UPLOAD_INTERVAL = platform_config['bilibili']['upload_interval']
        self.BILIBILI_MAX_DAILY_UPLOADS = platform_config['bilibili']['max_daily_uploads']
        
        # 小红书配置
        self.XIAOHONGSHU_UPLOAD_INTERVAL = platform_config['xiaohongshu']['upload_interval']
        self.XIAOHONGSHU_MAX_DAILY_UPLOADS = platform_config['xiaohongshu']['max_daily_uploads']
        
        # 快手配置
        self.KUAISHOU_UPLOAD_INTERVAL = platform_config['kuaishou']['upload_interval']
        self.KUAISHOU_MAX_DAILY_UPLOADS = platform_config['kuaishou']['max_daily_uploads']
        
        # YouTube配置
        self.YOUTUBE_UPLOAD_INTERVAL = platform_config['youtube']['upload_interval']
        self.YOUTUBE_MAX_DAILY_UPLOADS = platform_config['youtube']['max_daily_uploads']
        
        # 发布调度配置
        self.PUBLISH_TIME_RANGE = {
            "start": "09:00",
            "end": "22:00"
        }

# 日志配置类
class LogConfig:
    """日志配置"""
    def __init__(self):
        system_config = env_config.get_system_config()
        
        self.LOG_LEVEL = system_config['log_level']
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.LOG_FILE = LOGS_DIR / "pipeline.log"
        self.DEBUG = system_config['debug']

# 内容审核配置类
class ReviewConfig:
    """内容审核配置"""
    def __init__(self):
        review_config = env_config.get_content_review_config()
        
        # 敏感词检测
        self.SENSITIVE_WORDS_FILE = PROJECT_ROOT / "config" / "sensitive_words.txt"
        
        # 审核阈值
        self.SENSITIVITY_THRESHOLD = review_config['sensitive_words_threshold']
        
        # 自动审核开关
        self.AUTO_REVIEW_ENABLED = review_config['auto_review_enabled']
        self.CONTENT_REVIEW_ENABLED = review_config['enabled']

# 存储配置类
class StorageConfig:
    """存储配置"""
    def __init__(self):
        storage_config = env_config.get_storage_config()
        
        self.UPLOAD_FOLDER = Path(storage_config['upload_folder'])
        self.TEMP_FOLDER = Path(storage_config['temp_folder'])
        self.MAX_CONTENT_LENGTH = storage_config['max_content_length']
        self.ALLOWED_EXTENSIONS = storage_config['allowed_extensions']

# 安全配置类
class SecurityConfig:
    """安全配置"""
    def __init__(self):
        security_config = env_config.get_security_config()
        
        self.SECRET_KEY = security_config['secret_key']
        self.JWT_SECRET_KEY = security_config['jwt_secret_key']
        self.SESSION_TIMEOUT = security_config['session_timeout']

# 系统配置类
class SystemConfig:
    """系统配置"""
    def __init__(self):
        system_config = env_config.get_system_config()
        
        self.DEBUG = system_config['debug']
        self.HOST = system_config['host']
        self.PORT = system_config['port']
        self.WORKERS = system_config['workers']

# 监控配置类
class MonitoringConfig:
    """监控配置"""
    def __init__(self):
        monitoring_config = env_config.get_monitoring_config()
        
        self.ENABLED = monitoring_config['enabled']
        self.METRICS_RETENTION_DAYS = monitoring_config['metrics_retention_days']
        self.ALERT_EMAIL_ENABLED = monitoring_config['alert_email_enabled']
        self.ALERT_WEBHOOK_URL = monitoring_config['alert_webhook_url']

# 任务调度配置类
class SchedulerConfig:
    """任务调度配置"""
    def __init__(self):
        scheduler_config = env_config.get_scheduler_config()
        
        self.ENABLED = scheduler_config['enabled']
        self.MAX_CONCURRENT_TASKS = scheduler_config['max_concurrent_tasks']
        self.TASK_TIMEOUT = scheduler_config['task_timeout']
        self.RETRY_ATTEMPTS = scheduler_config['retry_attempts']

# 数据分析配置类
class AnalyticsConfig:
    """数据分析配置"""
    def __init__(self):
        analytics_config = env_config.get_analytics_config()
        
        self.ENABLED = analytics_config['enabled']
        self.RETENTION_DAYS = analytics_config['retention_days']
        self.EXPORT_FORMAT = analytics_config['export_format']

# 备份配置类
class BackupConfig:
    """备份配置"""
    def __init__(self):
        backup_config = env_config.get_backup_config()
        
        self.ENABLED = backup_config['enabled']
        self.INTERVAL = backup_config['interval']
        self.RETENTION_DAYS = backup_config['retention_days']
        self.LOCATION = Path(backup_config['location'])

# 创建配置实例
api_config = APIConfig()
database_config = DatabaseConfig()
video_config = VideoConfig()
upload_config = UploadConfig()
log_config = LogConfig()
review_config = ReviewConfig()
storage_config = StorageConfig()
security_config = SecurityConfig()
system_config = SystemConfig()
monitoring_config = MonitoringConfig()
scheduler_config = SchedulerConfig()
analytics_config = AnalyticsConfig()
backup_config = BackupConfig()
