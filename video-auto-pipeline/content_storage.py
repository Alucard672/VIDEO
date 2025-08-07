#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容存储管理器
负责管理采集到的新闻内容的存储、检索和管理
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

# 配置日志
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from config import DATABASE_PATH
except ImportError:
    DATABASE_PATH = project_root / "data" / "content.db"

class ContentStorage:
    """内容存储管理器"""
    
    def __init__(self):
        # 使用专门的内容数据库
        self.db_path = project_root / "data" / "content.db"
        self._init_database()
    
    def _init_database(self):
        """初始化内容数据库"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建采集内容表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collected_articles (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    title TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    source TEXT,
                    source_url TEXT,
                    author TEXT,
                    publish_time DATETIME,
                    category TEXT,
                    tags TEXT,
                    image_url TEXT,
                    word_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'raw',
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            
            # 创建内容分类表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT DEFAULT '#007bff',
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建内容标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建内容处理记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_processing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    process_type TEXT NOT NULL,
                    process_status TEXT DEFAULT 'pending',
                    process_result TEXT,
                    process_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES collected_articles (id)
                )
            ''')
            
            # 插入默认分类
            default_categories = [
                ('科技', '科技新闻和数码产品', '#28a745'),
                ('娱乐', '娱乐八卦和明星动态', '#dc3545'),
                ('财经', '财经新闻和商业资讯', '#ffc107'),
                ('体育', '体育赛事和运动新闻', '#17a2b8'),
                ('社会', '社会新闻和民生话题', '#6c757d'),
                ('国际', '国际新闻和全球动态', '#6f42c1'),
                ('教育', '教育资讯和学习内容', '#fd7e14'),
                ('健康', '健康养生和医疗资讯', '#20c997')
            ]
            
            for name, desc, color in default_categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO content_categories (name, description, color)
                    VALUES (?, ?, ?)
                ''', (name, desc, color))
            
            conn.commit()
            conn.close()
            
            logger.info("内容存储数据库初始化完成")
            
        except Exception as e:
            logger.error(f"内容存储数据库初始化失败: {e}")
            raise
    
    def save_articles(self, task_id: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """保存采集到的文章"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            failed_count = 0
            
            for article in articles:
                try:
                    article_id = str(uuid.uuid4())
                    
                    # 处理发布时间
                    publish_time = None
                    if article.get('publish_time'):
                        if isinstance(article['publish_time'], str):
                            try:
                                publish_time = datetime.fromisoformat(article['publish_time'].replace('T', ' '))
                            except:
                                publish_time = datetime.now()
                        elif isinstance(article['publish_time'], datetime):
                            publish_time = article['publish_time']
                    
                    # 计算字数
                    content = article.get('content', '')
                    word_count = len(content.replace(' ', '').replace('\n', ''))
                    
                    # 处理标签
                    tags = article.get('tags', [])
                    if isinstance(tags, list):
                        tags = ','.join(tags)
                    
                    cursor.execute('''
                        INSERT INTO collected_articles 
                        (id, task_id, title, content, summary, source, source_url, 
                         author, publish_time, category, tags, image_url, word_count, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article_id, task_id, article.get('title', ''),
                        content, article.get('summary', ''),
                        article.get('source', ''), article.get('source_url', ''),
                        article.get('author', ''), publish_time,
                        article.get('category', '未分类'), tags,
                        article.get('image_url', ''), word_count, 'raw'
                    ))
                    
                    saved_count += 1
                    
                    # 更新标签使用次数
                    if article.get('tags'):
                        tag_list = article['tags'] if isinstance(article['tags'], list) else article['tags'].split(',')
                        for tag in tag_list:
                            tag = tag.strip()
                            if tag:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO content_tags (name, usage_count)
                                    VALUES (?, 0)
                                ''', (tag,))
                                cursor.execute('''
                                    UPDATE content_tags SET usage_count = usage_count + 1
                                    WHERE name = ?
                                ''', (tag,))
                    
                except Exception as e:
                    logger.error(f"保存文章失败: {e}")
                    failed_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"文章保存完成: 成功 {saved_count} 篇, 失败 {failed_count} 篇")
            
            return {
                'success': True,
                'saved_count': saved_count,
                'failed_count': failed_count,
                'total_count': len(articles)
            }
            
        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0,
                'failed_count': len(articles),
                'total_count': len(articles)
            }
    
    def get_articles_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID获取文章"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, summary, source, source_url, author,
                       publish_time, category, tags, image_url, word_count, status,
                       created_time, updated_time
                FROM collected_articles
                WHERE task_id = ?
                ORDER BY created_time DESC
            ''', (task_id,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'summary': row[3],
                    'source': row[4],
                    'source_url': row[5],
                    'author': row[6],
                    'publish_time': row[7],
                    'category': row[8],
                    'tags': row[9].split(',') if row[9] else [],
                    'image_url': row[10],
                    'word_count': row[11],
                    'status': row[12],
                    'created_time': row[13],
                    'updated_time': row[14]
                })
            
            conn.close()
            return articles
            
        except Exception as e:
            logger.error(f"获取任务文章失败: {e}")
            return []
    
    def get_recent_articles(self, limit: int = 50, category: str = None, 
                          status: str = None) -> List[Dict[str, Any]]:
        """获取最近的文章"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f'''
                SELECT id, task_id, title, content, summary, source, source_url, author,
                       publish_time, category, tags, image_url, word_count, status,
                       created_time, updated_time
                FROM collected_articles
                {where_clause}
                ORDER BY created_time DESC
                LIMIT ?
            '''
            
            params.append(limit)
            cursor.execute(query, params)
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'task_id': row[1],
                    'title': row[2],
                    'content': row[3],
                    'summary': row[4],
                    'source': row[5],
                    'source_url': row[6],
                    'author': row[7],
                    'publish_time': row[8],
                    'category': row[9],
                    'tags': row[10].split(',') if row[10] else [],
                    'image_url': row[11],
                    'word_count': row[12],
                    'status': row[13],
                    'created_time': row[14],
                    'updated_time': row[15]
                })
            
            conn.close()
            return articles
            
        except Exception as e:
            logger.error(f"获取最近文章失败: {e}")
            return []
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """获取内容统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总体统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_articles,
                    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed_articles,
                    SUM(CASE WHEN status = 'raw' THEN 1 ELSE 0 END) as raw_articles,
                    SUM(word_count) as total_words,
                    AVG(word_count) as avg_words
                FROM collected_articles
            ''')
            
            row = cursor.fetchone()
            total_stats = {
                'total_articles': row[0] or 0,
                'processed_articles': row[1] or 0,
                'raw_articles': row[2] or 0,
                'total_words': row[3] or 0,
                'avg_words': int(row[4] or 0)
            }
            
            # 分类统计
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM collected_articles
                GROUP BY category
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            category_stats = []
            for row in cursor.fetchall():
                category_stats.append({
                    'category': row[0],
                    'count': row[1]
                })
            
            # 来源统计
            cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM collected_articles
                WHERE source IS NOT NULL AND source != ''
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            source_stats = []
            for row in cursor.fetchall():
                source_stats.append({
                    'source': row[0],
                    'count': row[1]
                })
            
            conn.close()
            
            return {
                'total_stats': total_stats,
                'category_stats': category_stats,
                'source_stats': source_stats
            }
            
        except Exception as e:
            logger.error(f"获取内容统计失败: {e}")
            return {
                'total_stats': {'total_articles': 0, 'processed_articles': 0, 'raw_articles': 0, 'total_words': 0, 'avg_words': 0},
                'category_stats': [],
                'source_stats': []
            }

# 全局实例
content_storage = ContentStorage()

if __name__ == "__main__":
    print("=== 内容存储管理器测试 ===")
    
    # 测试保存文章
    test_articles = [
        {
            'title': '测试新闻1：AI技术发展迅速',
            'content': '人工智能技术在各个领域都取得了显著进展，特别是在自然语言处理和计算机视觉方面...',
            'summary': '人工智能技术快速发展，在多个领域取得突破',
            'source': '科技日报',
            'source_url': 'https://example.com/news1',
            'author': '张三',
            'category': '科技',
            'tags': ['人工智能', '科技', '发展']
        },
        {
            'title': '测试新闻2：新能源汽车市场火热',
            'content': '新能源汽车市场持续升温，各大厂商纷纷推出新产品，消费者接受度不断提高...',
            'summary': '新能源汽车市场快速发展，消费者接受度提升',
            'source': '汽车之家',
            'source_url': 'https://example.com/news2',
            'author': '李四',
            'category': '科技',
            'tags': ['新能源', '汽车', '市场']
        }
    ]
    
    result = content_storage.save_articles('test-task-id', test_articles)
    print(f"保存结果: {result}")
    
    # 测试获取文章
    articles = content_storage.get_recent_articles(10)
    print(f"获取到 {len(articles)} 篇文章")
    
    # 测试统计
    stats = content_storage.get_content_statistics()
    print(f"内容统计: {stats}")
    
    print("内容存储管理器测试完成")