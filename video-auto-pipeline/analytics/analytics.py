#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块
提供视频发布数据统计、分析和报告功能
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

class VideoAnalytics:
    """视频数据分析器"""
    
    def __init__(self):
        self.db_path = Path("data/analytics.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建视频统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                publish_time DATETIME NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                duration INTEGER DEFAULT 0,
                category TEXT,
                tags TEXT,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建平台统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platform_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                date DATE NOT NULL,
                total_videos INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_likes INTEGER DEFAULT 0,
                total_comments INTEGER DEFAULT 0,
                avg_engagement_rate REAL DEFAULT 0.0,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, date)
            )
        ''')
        
        # 创建热门话题表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                platform TEXT NOT NULL,
                mention_count INTEGER DEFAULT 0,
                engagement_score REAL DEFAULT 0.0,
                date DATE NOT NULL,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据分析数据库初始化完成")
    
    def record_video_stats(self, video_data: Dict) -> bool:
        """记录视频统计数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO video_stats 
                (video_id, platform, title, publish_time, views, likes, comments, shares, duration, category, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data.get("video_id"),
                video_data.get("platform"),
                video_data.get("title"),
                video_data.get("publish_time"),
                video_data.get("views", 0),
                video_data.get("likes", 0),
                video_data.get("comments", 0),
                video_data.get("shares", 0),
                video_data.get("duration", 0),
                video_data.get("category"),
                json.dumps(video_data.get("tags", []))
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"视频统计数据记录成功: {video_data.get('title')}")
            return True
            
        except Exception as e:
            logger.error(f"记录视频统计数据失败: {e}")
            return False
    
    def get_platform_summary(self, platform: str, days: int = 30) -> Dict:
        """获取平台数据摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 查询统计数据
        cursor.execute('''
            SELECT 
                COUNT(*) as total_videos,
                SUM(views) as total_views,
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                SUM(shares) as total_shares,
                AVG(views) as avg_views,
                AVG(likes) as avg_likes
            FROM video_stats 
            WHERE platform = ? AND publish_time >= ? AND publish_time <= ?
        ''', (platform, start_date.isoformat(), end_date.isoformat()))
        
        result = cursor.fetchone()
        
        summary = {
            "platform": platform,
            "period_days": days,
            "total_videos": result[0] or 0,
            "total_views": result[1] or 0,
            "total_likes": result[2] or 0,
            "total_comments": result[3] or 0,
            "total_shares": result[4] or 0,
            "avg_views": round(result[5] or 0, 2),
            "avg_likes": round(result[6] or 0, 2),
            "engagement_rate": 0.0
        }
        
        # 计算互动率
        if summary["total_views"] > 0:
            total_engagement = summary["total_likes"] + summary["total_comments"] + summary["total_shares"]
            summary["engagement_rate"] = round((total_engagement / summary["total_views"]) * 100, 2)
        
        conn.close()
        return summary
    
    def get_trending_analysis(self, platform: str = None, days: int = 7) -> List[Dict]:
        """获取热门趋势分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询条件
        where_clause = "WHERE publish_time >= ? AND publish_time <= ?"
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if platform:
            where_clause += " AND platform = ?"
            params.append(platform)
        
        # 查询热门视频
        cursor.execute(f'''
            SELECT title, platform, views, likes, comments, shares, publish_time
            FROM video_stats 
            {where_clause}
            ORDER BY views DESC
            LIMIT 10
        ''', params)
        
        trending_videos = []
        for row in cursor.fetchall():
            video = {
                "title": row[0],
                "platform": row[1],
                "views": row[2],
                "likes": row[3],
                "comments": row[4],
                "shares": row[5],
                "publish_time": row[6],
                "engagement_rate": 0.0
            }
            
            # 计算互动率
            if video["views"] > 0:
                total_engagement = video["likes"] + video["comments"] + video["shares"]
                video["engagement_rate"] = round((total_engagement / video["views"]) * 100, 2)
            
            trending_videos.append(video)
        
        conn.close()
        return trending_videos
    
    def generate_daily_report(self, date: str = None) -> Dict:
        """生成日报"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查询当日数据
        cursor.execute('''
            SELECT platform, COUNT(*) as video_count, SUM(views) as total_views, 
                   SUM(likes) as total_likes, SUM(comments) as total_comments
            FROM video_stats 
            WHERE DATE(publish_time) = ?
            GROUP BY platform
        ''', (date,))
        
        platform_data = {}
        for row in cursor.fetchall():
            platform_data[row[0]] = {
                "video_count": row[1],
                "total_views": row[2] or 0,
                "total_likes": row[3] or 0,
                "total_comments": row[4] or 0
            }
        
        # 查询总体数据
        cursor.execute('''
            SELECT COUNT(*) as total_videos, SUM(views) as total_views,
                   SUM(likes) as total_likes, SUM(comments) as total_comments
            FROM video_stats 
            WHERE DATE(publish_time) = ?
        ''', (date,))
        
        total_result = cursor.fetchone()
        
        report = {
            "date": date,
            "summary": {
                "total_videos": total_result[0] or 0,
                "total_views": total_result[1] or 0,
                "total_likes": total_result[2] or 0,
                "total_comments": total_result[3] or 0
            },
            "platforms": platform_data,
            "generated_time": datetime.now().isoformat()
        }
        
        conn.close()
        return report
    
    def create_performance_chart(self, platform: str, days: int = 30) -> str:
        """创建性能图表"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 查询数据
            query = '''
                SELECT DATE(publish_time) as date, SUM(views) as daily_views, 
                       SUM(likes) as daily_likes, COUNT(*) as daily_videos
                FROM video_stats 
                WHERE platform = ? AND publish_time >= ?
                GROUP BY DATE(publish_time)
                ORDER BY date
            '''
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = pd.read_sql_query(query, conn, params=[platform, start_date.isoformat()])
            conn.close()
            
            if df.empty:
                logger.warning(f"没有找到平台 {platform} 的数据")
                return ""
            
            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'{platform} 平台性能分析 (最近{days}天)', fontsize=16)
            
            # 日观看量趋势
            ax1.plot(df['date'], df['daily_views'], marker='o', color='blue')
            ax1.set_title('日观看量趋势')
            ax1.set_ylabel('观看量')
            ax1.tick_params(axis='x', rotation=45)
            
            # 日点赞量趋势
            ax2.plot(df['date'], df['daily_likes'], marker='s', color='red')
            ax2.set_title('日点赞量趋势')
            ax2.set_ylabel('点赞量')
            ax2.tick_params(axis='x', rotation=45)
            
            # 日发布视频数量
            ax3.bar(df['date'], df['daily_videos'], color='green', alpha=0.7)
            ax3.set_title('日发布视频数量')
            ax3.set_ylabel('视频数量')
            ax3.tick_params(axis='x', rotation=45)
            
            # 平均每视频观看量
            avg_views = df['daily_views'] / df['daily_videos']
            ax4.plot(df['date'], avg_views, marker='d', color='orange')
            ax4.set_title('平均每视频观看量')
            ax4.set_ylabel('平均观看量')
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = Path("data/charts")
            chart_path.mkdir(exist_ok=True)
            
            filename = f"{platform}_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = chart_path / filename
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"性能图表已生成: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"生成性能图表失败: {e}")
            return ""
    
    def export_data(self, platform: str = None, start_date: str = None, end_date: str = None) -> str:
        """导出数据到CSV"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 构建查询
            where_conditions = []
            params = []
            
            if platform:
                where_conditions.append("platform = ?")
                params.append(platform)
            
            if start_date:
                where_conditions.append("publish_time >= ?")
                params.append(start_date)
            
            if end_date:
                where_conditions.append("publish_time <= ?")
                params.append(end_date)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f'''
                SELECT video_id, platform, title, publish_time, views, likes, 
                       comments, shares, duration, category, tags
                FROM video_stats 
                {where_clause}
                ORDER BY publish_time DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # 导出文件
            export_path = Path("data/exports")
            export_path.mkdir(exist_ok=True)
            
            filename = f"video_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = export_path / filename
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            logger.info(f"数据导出完成: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            return ""

def main():
    """主函数"""
    analytics = VideoAnalytics()
    
    # 测试数据记录
    test_data = {
        "video_id": "test_001",
        "platform": "douyin",
        "title": "测试视频标题",
        "publish_time": datetime.now().isoformat(),
        "views": 1000,
        "likes": 50,
        "comments": 10,
        "shares": 5,
        "duration": 60,
        "category": "娱乐",
        "tags": ["测试", "视频"]
    }
    
    analytics.record_video_stats(test_data)
    
    # 生成报告
    summary = analytics.get_platform_summary("douyin", 30)
    print(f"平台摘要: {summary}")
    
    daily_report = analytics.generate_daily_report()
    print(f"日报: {daily_report}")

if __name__ == "__main__":
    main()