#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库字段不匹配问题
"""

import sqlite3
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_fields():
    """修复数据库字段不匹配问题"""
    
    # 数据库文件路径
    db_files = [
        'tasks.db',
        'data/video_pipeline.db'
    ]
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            logger.info(f"数据库文件不存在，跳过: {db_file}")
            continue
            
        logger.info(f"修复数据库: {db_file}")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 检查并修复tasks表
            fix_tasks_table(cursor, conn)
            
            # 检查并修复users表
            fix_users_table(cursor, conn)
            
            # 检查并修复content表
            fix_content_table(cursor, conn)
            
            conn.close()
            logger.info(f"数据库修复完成: {db_file}")
            
        except Exception as e:
            logger.error(f"修复数据库失败 {db_file}: {e}")

def fix_tasks_table(cursor, conn):
    """修复tasks表字段"""
    try:
        # 检查tasks表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if not cursor.fetchone():
            logger.info("tasks表不存在，跳过修复")
            return
        
        # 获取当前表结构
        cursor.execute("PRAGMA table_info(tasks)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        logger.info(f"tasks表当前字段: {list(columns.keys())}")
        
        # 需要添加的字段
        fields_to_add = [
            ('created_time', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('started_time', 'DATETIME'),
            ('completed_time', 'DATETIME'),
            ('scheduled_time', 'DATETIME'),
            ('retry_count', 'INTEGER DEFAULT 0'),
            ('max_retries', 'INTEGER DEFAULT 3'),
            ('timeout', 'INTEGER DEFAULT 3600'),
            ('dependencies', 'TEXT'),
            ('priority', 'INTEGER DEFAULT 2'),
            ('task_name', 'TEXT'),
            ('params', 'TEXT'),
            ('error_message', 'TEXT')
        ]
        
        # 添加缺失的字段
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {field_name} {field_type}")
                    logger.info(f"添加字段到tasks表: {field_name}")
                except sqlite3.Error as e:
                    logger.warning(f"添加字段失败 {field_name}: {e}")
        
        # 如果存在category字段但不存在content_type字段，重命名
        if 'category' in columns and 'content_type' not in columns:
            try:
                cursor.execute("ALTER TABLE tasks ADD COLUMN content_type TEXT")
                cursor.execute("UPDATE tasks SET content_type = category WHERE category IS NOT NULL")
                logger.info("将category字段内容复制到content_type字段")
            except sqlite3.Error as e:
                logger.warning(f"处理category字段失败: {e}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"修复tasks表失败: {e}")

def fix_users_table(cursor, conn):
    """修复users表字段"""
    try:
        # 检查users表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.info("users表不存在，跳过修复")
            return
        
        # 获取当前表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        logger.info(f"users表当前字段: {list(columns.keys())}")
        
        # 需要添加的字段
        fields_to_add = [
            ('last_login', 'DATETIME'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
        ]
        
        # 添加缺失的字段
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                    logger.info(f"添加字段到users表: {field_name}")
                except sqlite3.Error as e:
                    logger.warning(f"添加字段失败 {field_name}: {e}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"修复users表失败: {e}")

def fix_content_table(cursor, conn):
    """修复content表字段"""
    try:
        # 检查content表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content'")
        if not cursor.fetchone():
            logger.info("content表不存在，跳过修复")
            return
        
        # 获取当前表结构
        cursor.execute("PRAGMA table_info(content)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        logger.info(f"content表当前字段: {list(columns.keys())}")
        
        # 需要添加的字段
        fields_to_add = [
            ('content_type', 'TEXT'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
        ]
        
        # 添加缺失的字段
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE content ADD COLUMN {field_name} {field_type}")
                    logger.info(f"添加字段到content表: {field_name}")
                except sqlite3.Error as e:
                    logger.warning(f"添加字段失败 {field_name}: {e}")
        
        # 如果存在category字段但不存在content_type字段，复制数据
        if 'category' in columns and 'content_type' in columns:
            try:
                cursor.execute("UPDATE content SET content_type = category WHERE category IS NOT NULL AND content_type IS NULL")
                logger.info("将category字段内容复制到content_type字段")
            except sqlite3.Error as e:
                logger.warning(f"复制category到content_type失败: {e}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"修复content表失败: {e}")

def check_database_structure():
    """检查数据库结构"""
    db_files = [
        'tasks.db',
        'data/video_pipeline.db'
    ]
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            continue
            
        logger.info(f"\n=== 检查数据库结构: {db_file} ===")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                logger.info(f"\n表: {table}")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    logger.info(f"  {col[1]} ({col[2]})")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"检查数据库结构失败 {db_file}: {e}")

if __name__ == "__main__":
    print("=== 修复数据库字段不匹配问题 ===")
    
    # 检查修复前的结构
    logger.info("修复前的数据库结构:")
    check_database_structure()
    
    # 执行修复
    fix_database_fields()
    
    # 检查修复后的结构
    logger.info("\n修复后的数据库结构:")
    check_database_structure()
    
    print("数据库字段修复完成")