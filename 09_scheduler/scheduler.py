#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布调度模块
提供智能调度、账号轮播、发布时间优化等功能
"""

import time
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
import sqlite3
from config import UploadConfig

class PublishScheduler:
    """发布调度器"""
    
    def __init__(self):
        self.db_path = Path("data/scheduler.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # 平台最佳发布时间
        self.optimal_times = {
            "douyin": {
                "weekdays": ["09:00", "12:00", "18:00", "21:00"],
                "weekends": ["10:00", "14:00", "19:00", "22:00"],
                "min_interval": 3600,  # 1小时
                "max_daily": 5
            },
            "bilibili": {
                "weekdays": ["10:00", "14:00", "19:00", "22:00"],
                "weekends": ["11:00", "15:00", "20:00", "23:00"],
                "min_interval": 7200,  # 2小时
                "max_daily": 3
            }
        }
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建调度任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS publish_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_path TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                platform TEXT NOT NULL,
                account_id INTEGER,
                scheduled_time DATETIME NOT NULL,
                status TEXT DEFAULT 'pending',
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("调度数据库初始化完成")
    
    def schedule_video_publish(self, video_info: Dict, platform: str, 
                             account_id: Optional[int] = None) -> Dict:
        """调度视频发布"""
        logger.info(f"开始调度视频发布，平台: {platform}")
        
        # 获取最佳发布时间
        optimal_time = self._get_optimal_publish_time(platform, account_id)
        
        # 创建发布任务
        task_data = {
            "video_path": video_info["video_path"],
            "title": video_info["title"],
            "description": video_info.get("description", ""),
            "tags": json.dumps(video_info.get("tags", [])),
            "platform": platform,
            "account_id": account_id,
            "scheduled_time": optimal_time.isoformat(),
            "status": "pending"
        }
        
        # 保存到数据库
        task_id = self._save_publish_task(task_data)
        
        result = {
            "task_id": task_id,
            "scheduled_time": optimal_time.isoformat(),
            "platform": platform,
            "account_id": account_id,
            "status": "scheduled"
        }
        
        logger.info(f"视频发布调度完成，任务ID: {task_id}")
        return result
    
    def _get_optimal_publish_time(self, platform: str, account_id: Optional[int] = None) -> datetime:
        """获取最佳发布时间"""
        now = datetime.now()
        
        # 获取平台最佳时间
        if platform in self.optimal_times:
            platform_times = self.optimal_times[platform]
            
            # 判断是工作日还是周末
            is_weekend = now.weekday() >= 5
            time_list = platform_times["weekends"] if is_weekend else platform_times["weekdays"]
            
            # 找到下一个最佳时间
            for time_str in time_list:
                hour, minute = map(int, time_str.split(":"))
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 如果时间已过，选择下一个时间
                if target_time <= now:
                    continue
                
                return target_time
            
            # 如果今天没有合适时间，安排到明天
            tomorrow = now + timedelta(days=1)
            hour, minute = map(int, time_list[0].split(":"))
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 默认安排到1小时后
        return now + timedelta(hours=1)
    
    def _save_publish_task(self, task_data: Dict) -> int:
        """保存发布任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO publish_tasks 
            (video_path, title, description, tags, platform, account_id, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_data["video_path"],
            task_data["title"],
            task_data["description"],
            task_data["tags"],
            task_data["platform"],
            task_data["account_id"],
            task_data["scheduled_time"],
            task_data["status"]
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def get_pending_tasks(self, platform: Optional[str] = None) -> List[Dict]:
        """获取待发布任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if platform:
            cursor.execute('''
                SELECT * FROM publish_tasks 
                WHERE status = 'pending' AND platform = ?
                ORDER BY scheduled_time ASC
            ''', (platform,))
        else:
            cursor.execute('''
                SELECT * FROM publish_tasks 
                WHERE status = 'pending'
                ORDER BY scheduled_time ASC
            ''')
        
        tasks = []
        for row in cursor.fetchall():
            task = {
                "id": row[0],
                "video_path": row[1],
                "title": row[2],
                "description": row[3],
                "tags": json.loads(row[4]) if row[4] else [],
                "platform": row[5],
                "account_id": row[6],
                "scheduled_time": row[7],
                "status": row[8]
            }
            tasks.append(task)
        
        conn.close()
        return tasks

def main():
    """主函数"""
    scheduler = PublishScheduler()
    
    # 测试调度功能
    video_info = {
        "video_path": "test_video.mp4",
        "title": "测试视频标题",
        "description": "这是一个测试视频",
        "tags": ["测试", "视频"]
    }
    
    result = scheduler.schedule_video_publish(video_info, "douyin", 1)
    print(f"调度结果: {result}")

if __name__ == "__main__":
    main() 