#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API配置文件
管理各种第三方API的密钥和设置
"""

import os
from pathlib import Path

class APIConfig:
    """API配置管理类"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.env_file = self.config_dir / ".env"
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        # 默认配置
        self.config = {
            # 新闻API配置
            'news_api_key': os.getenv('NEWS_API_KEY', ''),
            'news_api_url': 'https://newsapi.org/v2/top-headlines',
            
            # YouTube API配置
            'youtube_api_key': os.getenv('YOUTUBE_API_KEY', ''),
            'youtube_api_url': 'https://www.googleapis.com/youtube/v3',
            
            # B站API配置
            'bilibili_api_url': 'https://api.bilibili.com',
            
            # 网易新闻API
            'netease_api_url': 'https://3g.163.com/touch/reconstruct/article/list',
            
            # 新浪新闻API
            'sina_api_url': 'https://interface.sina.cn/news/get_news_by_channel',
            
            # 其他配置
            'request_timeout': 10,
            'max_retries': 3,
            'cache_duration': 300,  # 5分钟缓存
        }
        
        # 从.env文件加载配置
        if self.env_file.exists():
            self.load_env_file()
    
    def load_env_file(self):
        """从.env文件加载环境变量"""
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
        except Exception as e:
            print(f"加载.env文件失败: {e}")
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
    
    def save_config(self):
        """保存配置到.env文件"""
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write("# API配置文件\n")
                f.write("# 请在此文件中配置您的API密钥\n\n")
                
                for key, value in self.config.items():
                    if key not in ['request_timeout', 'max_retries', 'cache_duration']:
                        f.write(f"{key}={value}\n")
                
                f.write(f"\n# 其他设置\n")
                f.write(f"request_timeout={self.config['request_timeout']}\n")
                f.write(f"max_retries={self.config['max_retries']}\n")
                f.write(f"cache_duration={self.config['cache_duration']}\n")
                
            print("配置已保存到.env文件")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def is_api_configured(self, api_name):
        """检查API是否已配置"""
        api_keys = {
            'news': 'news_api_key',
            'youtube': 'youtube_api_key',
            'bilibili': 'bilibili_api_url',
            'netease': 'netease_api_url',
            'sina': 'sina_api_url'
        }
        
        key = api_keys.get(api_name)
        if key:
            return bool(self.get(key))
        return False
    
    def get_api_status(self):
        """获取所有API的配置状态"""
        return {
            'news_api': self.is_api_configured('news'),
            'youtube_api': self.is_api_configured('youtube'),
            'bilibili_api': self.is_api_configured('bilibili'),
            'netease_api': self.is_api_configured('netease'),
            'sina_api': self.is_api_configured('sina')
        }

# 创建全局配置实例
api_config = APIConfig()

if __name__ == '__main__':
    # 测试配置
    print("API配置状态:")
    for api, status in api_config.get_api_status().items():
        print(f"  {api}: {'已配置' if status else '未配置'}")
    
    # 创建示例.env文件
    if not api_config.env_file.exists():
        api_config.save_config()
        print("\n已创建示例.env文件，请在其中配置您的API密钥") 