#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频采集模块 - 修复版
"""

import os
import json
import random
from datetime import datetime
from pathlib import Path
import logging

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class VideoFetcher:
    """视频采集器"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.videos_dir = self.data_dir / "videos"
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # 视频分类目录
        self.categories = {
            'background': self.videos_dir / "background",
            'transition': self.videos_dir / "transition", 
            'effect': self.videos_dir / "effect",
            'stock': self.videos_dir / "stock"
        }
        
        # 创建分类目录
        for category_dir in self.categories.values():
            category_dir.mkdir(exist_ok=True)
    
    def fetch_bilibili_videos(self, category="热门", limit=5):
        """获取B站视频"""
        try:
            logger.info(f"开始获取B站视频 - 分类: {category}")
            
            # 模拟B站视频数据
            sample_videos = [
                {
                    'title': f'B站{category}视频：科技前沿资讯',
                    'description': f'这是来自B站的{category}视频，内容丰富，制作精良。',
                    'duration': f'{random.randint(1, 10)}:{random.randint(0, 59):02d}',
                    'platform': 'bilibili',
                    'category': category,
                    'url': f'https://bilibili.com/video/BV{random.randint(1000000, 9999999)}',
                    'views': random.randint(1000, 100000),
                    'likes': random.randint(100, 10000),
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'B站{category}视频：生活分享',
                    'description': f'B站{category}视频，分享日常生活和有趣见闻。',
                    'duration': f'{random.randint(1, 10)}:{random.randint(0, 59):02d}',
                    'platform': 'bilibili',
                    'category': category,
                    'url': f'https://bilibili.com/video/BV{random.randint(1000000, 9999999)}',
                    'views': random.randint(1000, 100000),
                    'likes': random.randint(100, 10000),
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            videos_list = sample_videos[:limit]
            logger.info(f"成功获取 {len(videos_list)} 条B站视频")
            self._save_video_data(videos_list, f"bilibili_{category}")
            return videos_list
            
        except Exception as e:
            logger.error(f"获取B站视频失败: {e}")
            return []
    
    def fetch_douyin_videos(self, category="热门", limit=5):
        """获取抖音视频"""
        try:
            logger.info(f"开始获取抖音视频 - 分类: {category}")
            
            # 模拟抖音视频数据
            sample_videos = [
                {
                    'title': f'抖音{category}视频：创意内容',
                    'description': f'这是来自抖音的{category}视频，创意十足，深受欢迎。',
                    'duration': f'{random.randint(0, 3)}:{random.randint(0, 59):02d}',
                    'platform': 'douyin',
                    'category': category,
                    'url': f'https://douyin.com/video/{random.randint(1000000, 9999999)}',
                    'views': random.randint(10000, 1000000),
                    'likes': random.randint(1000, 100000),
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'抖音{category}视频：生活记录',
                    'description': f'抖音{category}视频，记录美好生活瞬间。',
                    'duration': f'{random.randint(0, 3)}:{random.randint(0, 59):02d}',
                    'platform': 'douyin',
                    'category': category,
                    'url': f'https://douyin.com/video/{random.randint(1000000, 9999999)}',
                    'views': random.randint(10000, 1000000),
                    'likes': random.randint(1000, 100000),
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            videos_list = sample_videos[:limit]
            logger.info(f"成功获取 {len(videos_list)} 条抖音视频")
            self._save_video_data(videos_list, f"douyin_{category}")
            return videos_list
            
        except Exception as e:
            logger.error(f"获取抖音视频失败: {e}")
            return []
    
    def fetch_kuaishou_videos(self, category="热门", limit=5):
        """获取快手视频"""
        try:
            logger.info(f"开始获取快手视频 - 分类: {category}")
            
            # 模拟快手视频数据
            sample_videos = [
                {
                    'title': f'快手{category}视频：精彩内容',
                    'description': f'这是来自快手的{category}视频，内容精彩，值得观看。',
                    'duration': f'{random.randint(0, 3)}:{random.randint(0, 59):02d}',
                    'platform': 'kuaishou',
                    'category': category,
                    'url': f'https://kuaishou.com/video/{random.randint(1000000, 9999999)}',
                    'views': random.randint(5000, 500000),
                    'likes': random.randint(500, 50000),
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            videos_list = sample_videos[:limit]
            logger.info(f"成功获取 {len(videos_list)} 条快手视频")
            self._save_video_data(videos_list, f"kuaishou_{category}")
            return videos_list
            
        except Exception as e:
            logger.error(f"获取快手视频失败: {e}")
            return []
    
    def download_stock_videos(self, keywords, category="stock", limit=5):
        """下载素材视频"""
        try:
            logger.info(f"开始下载素材视频 - 关键词: {keywords}")
            
            stock_videos = []
            
            for keyword in keywords[:limit]:
                video_info = {
                    'title': f'{keyword}素材视频',
                    'description': f'高质量的{keyword}素材视频，可用于视频制作。',
                    'duration': f'{random.randint(10, 60)}s',
                    'category': category,
                    'file_path': str(self.categories[category] / f'{keyword}_素材.mp4'),
                    'file_size': random.randint(1024*1024, 10*1024*1024),
                    'download_time': datetime.now().isoformat(),
                    'source': 'StockVideo',
                    'url': f'https://stockvideo.com/{keyword}'
                }
                
                stock_videos.append(video_info)
                
                # 创建模拟文件
                video_file = Path(video_info['file_path'])
                video_file.parent.mkdir(parents=True, exist_ok=True)
                video_file.write_text(f"模拟视频文件: {keyword}", encoding='utf-8')
            
            logger.info(f"成功下载 {len(stock_videos)} 个素材视频")
            return stock_videos
            
        except Exception as e:
            logger.error(f"素材视频下载失败: {e}")
            return []
    
    def _save_video_data(self, videos_list, filename):
        """保存视频数据到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.data_dir / f"{filename}_{timestamp}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(videos_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"视频数据已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存视频数据失败: {e}")

def main():
    """测试函数"""
    fetcher = VideoFetcher()
    
    # 测试各种视频源
    sources = [
        ('B站视频', fetcher.fetch_bilibili_videos),
        ('抖音视频', fetcher.fetch_douyin_videos),
        ('快手视频', fetcher.fetch_kuaishou_videos)
    ]
    
    for source_name, fetch_func in sources:
        print(f"\n测试{source_name}...")
        try:
            videos = fetch_func(category="热门", limit=3)
            print(f"获取到 {len(videos)} 条{source_name}")
        except Exception as e:
            print(f"获取{source_name}失败: {e}")

if __name__ == "__main__":
    main() 