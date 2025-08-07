#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复内容数据库表结构
添加缺失的字段以匹配API需求
"""

import sqlite3
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "video_pipeline.db")

def fix_content_table():
    """修复内容表结构"""
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取现有表结构
        cursor.execute("PRAGMA table_info(content)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"现有字段: {existing_columns}")
        
        # 需要添加的字段
        new_columns = [
            ("content", "TEXT"),
            ("category", "TEXT"),
            ("source_url", "TEXT"),
            ("task_id", "INTEGER"),
            ("source_id", "INTEGER"),
            ("word_count", "INTEGER"),
            ("summary", "TEXT"),
            ("author", "TEXT"),
            ("publish_time", "TEXT"),
            ("content_url", "TEXT"),
            ("thumbnail_url", "TEXT"),
            ("view_count", "INTEGER DEFAULT 0"),
            ("like_count", "INTEGER DEFAULT 0"),
            ("comment_count", "INTEGER DEFAULT 0"),
            ("share_count", "INTEGER DEFAULT 0"),
            ("platform", "TEXT"),
            ("platform_id", "TEXT"),
            ("language", "TEXT DEFAULT 'zh-CN'"),
            ("quality_score", "REAL DEFAULT 0.0"),
            ("processed_at", "TEXT"),
            ("published_at", "TEXT")
        ]
        
        # 添加缺失的字段
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE content ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    logger.info(f"添加字段: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        logger.error(f"添加字段 {column_name} 失败: {e}")
        
        # 更新现有记录的默认值
        cursor.execute("UPDATE content SET content_type = category WHERE content_type IS NULL")
        cursor.execute("UPDATE content SET word_count = LENGTH(content) WHERE word_count IS NULL")
        cursor.execute("UPDATE content SET summary = SUBSTR(content, 1, 200) || '...' WHERE summary IS NULL AND content IS NOT NULL")
        cursor.execute("UPDATE content SET language = 'zh-CN' WHERE language IS NULL")
        cursor.execute("UPDATE content SET quality_score = 0.5 WHERE quality_score IS NULL")
        
        # 提交更改
        conn.commit()
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(content)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"更新后字段: {updated_columns}")
        
        # 插入一些测试数据（如果表为空）
        cursor.execute("SELECT COUNT(*) FROM content")
        content_count = cursor.fetchone()[0]
        
        if content_count == 0:
            logger.info("插入测试数据...")
            now = datetime.now().isoformat()
            
            test_content = [
                {
                    'title': '测试文章1：AI技术发展趋势',
                    'content': '人工智能技术正在快速发展，从机器学习到深度学习，再到大语言模型，AI正在改变我们的生活方式。本文将探讨AI技术的最新发展趋势，包括自然语言处理、计算机视觉、机器人技术等领域的突破。',
                    'category': '科技',
                    'content_type': '科技',
                    'tags': '["AI", "人工智能", "技术趋势", "机器学习"]',
                    'author': '科技观察员',
                    'word_count': 120,
                    'summary': '探讨AI技术的最新发展趋势，包括自然语言处理、计算机视觉等领域的突破。',
                    'created_at': now,
                    'status': 'raw',
                    'language': 'zh-CN',
                    'quality_score': 0.8
                },
                {
                    'title': '测试文章2：短视频内容创作技巧',
                    'content': '短视频已成为当下最受欢迎的内容形式之一。如何创作出吸引人的短视频内容？本文分享一些实用的创作技巧，包括选题策略、拍摄技巧、剪辑要点、发布时机等方面的经验。',
                    'category': '媒体',
                    'content_type': '媒体',
                    'tags': '["短视频", "内容创作", "拍摄技巧", "剪辑"]',
                    'author': '内容创作者',
                    'word_count': 95,
                    'summary': '分享短视频创作的实用技巧，包括选题、拍摄、剪辑、发布等方面的经验。',
                    'created_at': now,
                    'status': 'processed',
                    'language': 'zh-CN',
                    'quality_score': 0.9
                },
                {
                    'title': '测试文章3：数字营销策略解析',
                    'content': '数字营销在现代商业中扮演着越来越重要的角色。从社交媒体营销到搜索引擎优化，从内容营销到数据分析，企业需要掌握多种数字营销工具和策略。本文将深入分析当前主流的数字营销方法。',
                    'category': '营销',
                    'content_type': '营销',
                    'tags': '["数字营销", "社交媒体", "SEO", "内容营销"]',
                    'author': '营销专家',
                    'word_count': 110,
                    'summary': '深入分析当前主流的数字营销方法，包括社交媒体营销、SEO、内容营销等。',
                    'created_at': now,
                    'status': 'raw',
                    'language': 'zh-CN',
                    'quality_score': 0.7
                }
            ]
            
            for content in test_content:
                cursor.execute('''
                    INSERT INTO content (
                        title, content, category, content_type, tags, author, 
                        word_count, summary, created_at, status, language, quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    content['title'], content['content'], content['category'], 
                    content['content_type'], content['tags'], content['author'],
                    content['word_count'], content['summary'], content['created_at'],
                    content['status'], content['language'], content['quality_score']
                ))
            
            conn.commit()
            logger.info("测试数据插入完成")
        
        conn.close()
        logger.info("内容表结构修复完成")
        
    except Exception as e:
        logger.error(f"修复内容表结构失败: {e}")
        raise

def init_database():
    """初始化数据库（如果不存在）"""
    try:
        from database import init_db
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

if __name__ == "__main__":
    print("=== 修复内容数据库表结构 ===")
    
    # 初始化数据库
    init_database()
    
    # 修复内容表
    fix_content_table()
    
    print("内容数据库修复完成")