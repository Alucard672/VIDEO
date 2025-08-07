#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在tasks.db中创建内容表
"""

import sqlite3
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_content_table_in_tasks_db():
    """在tasks.db中创建内容表"""
    try:
        # 连接到tasks.db
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        
        # 检查是否已存在content表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content'")
        if cursor.fetchone():
            logger.info("content表已存在，删除重建...")
            cursor.execute("DROP TABLE content")
        
        # 创建content表
        cursor.execute('''
            CREATE TABLE content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                category TEXT,
                content_type TEXT,
                status TEXT DEFAULT 'raw',
                description TEXT,
                tags TEXT,
                source_url TEXT,
                task_id INTEGER,
                source_id INTEGER,
                word_count INTEGER,
                summary TEXT,
                author TEXT,
                publish_time TEXT,
                content_url TEXT,
                thumbnail_url TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                platform TEXT,
                platform_id TEXT,
                language TEXT DEFAULT 'zh-CN',
                quality_score REAL DEFAULT 0.0,
                processed_at TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        logger.info("content表创建成功")
        
        # 插入测试数据
        test_data = [
            {
                'title': '测试文章1',
                'content': '这是第一篇测试文章的内容，用于验证系统功能。',
                'category': '技术',
                'content_type': '文章',
                'status': 'processed',
                'description': '测试文章描述',
                'tags': '["测试", "技术"]',
                'author': '系统管理员',
                'word_count': 25,
                'summary': '这是第一篇测试文章的内容...',
                'language': 'zh-CN',
                'quality_score': 0.8
            },
            {
                'title': '测试文章2',
                'content': '这是第二篇测试文章的内容，包含更多的信息和数据。',
                'category': '生活',
                'content_type': '文章',
                'status': 'raw',
                'description': '生活类测试文章',
                'tags': '["测试", "生活"]',
                'author': '内容编辑',
                'word_count': 28,
                'summary': '这是第二篇测试文章的内容...',
                'language': 'zh-CN',
                'quality_score': 0.6
            },
            {
                'title': '测试视频内容',
                'content': '这是一个视频内容的描述，包含视频的基本信息和介绍。',
                'category': '娱乐',
                'content_type': '视频',
                'status': 'raw',
                'description': '娱乐视频内容',
                'tags': '["测试", "视频", "娱乐"]',
                'author': '视频创作者',
                'word_count': 32,
                'summary': '这是一个视频内容的描述...',
                'language': 'zh-CN',
                'quality_score': 0.7
            }
        ]
        
        for data in test_data:
            cursor.execute('''
                INSERT INTO content (
                    title, content, category, content_type, status, description, 
                    tags, author, word_count, summary, language, quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['title'], data['content'], data['category'], data['content_type'],
                data['status'], data['description'], data['tags'], data['author'],
                data['word_count'], data['summary'], data['language'], data['quality_score']
            ))
        
        conn.commit()
        logger.info("测试数据插入成功")
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM content")
        count = cursor.fetchone()[0]
        logger.info(f"content表中共有 {count} 条记录")
        
        # 显示表结构
        cursor.execute("PRAGMA table_info(content)")
        columns = cursor.fetchall()
        logger.info("content表结构:")
        for col in columns:
            logger.info(f"  {col[1]} {col[2]}")
        
        conn.close()
        logger.info("内容表创建完成")
        
    except Exception as e:
        logger.error(f"创建内容表失败: {e}")
        raise

if __name__ == "__main__":
    print("=== 在tasks.db中创建内容表 ===")
    create_content_table_in_tasks_db()
    print("内容表创建完成")