#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
提供数据库连接和初始化功能
"""

import sqlite3
import os
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "video_pipeline.db")

def init_db():
    """初始化数据库"""
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE,
                role TEXT DEFAULT 'user',
                created_at TEXT,
                last_login TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                config TEXT,
                result TEXT,
                error TEXT,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # 创建内容表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                category TEXT,
                tags TEXT,
                source_url TEXT,
                created_at TEXT,
                updated_at TEXT,
                task_id INTEGER,
                source_id INTEGER,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # 创建视频表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                video_url TEXT,
                thumbnail_url TEXT,
                duration INTEGER,
                category TEXT,
                tags TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT,
                updated_at TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                source_platform TEXT,
                source_id TEXT,
                task_id INTEGER,
                content_id INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (content_id) REFERENCES content (id)
            )
        ''')
        
        # 创建日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                timestamp TEXT,
                source TEXT,
                task_id INTEGER,
                user_id INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 创建采集任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fetch_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                source_ids TEXT,
                category_filters TEXT,
                total_limit INTEGER DEFAULT 50,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                result_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 创建API密钥表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                created_at TEXT,
                expires_at TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建统计数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_key TEXT NOT NULL,
                stat_value INTEGER DEFAULT 0,
                stat_date TEXT,
                UNIQUE(stat_key, stat_date)
            )
        ''')
        
        # 提交更改
        conn.commit()
        
        # 检查是否需要插入初始数据
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # 插入管理员用户
            from datetime import datetime
            now = datetime.now().isoformat()
            
            # 简单的密码哈希，实际应用中应使用更安全的方法
            import hashlib
            admin_password = hashlib.sha256("admin123".encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (username, password, email, role, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("admin", admin_password, "admin@example.com", "admin", now, "active"))
            
            # 插入一些初始配置
            configs = [
                ("system_name", "视频自动化流水线", "系统名称"),
                ("version", "1.0.0", "系统版本"),
                ("max_tasks", "10", "最大并发任务数"),
                ("default_video_quality", "720p", "默认视频质量"),
                ("enable_analytics", "true", "是否启用分析功能")
            ]
            
            for config in configs:
                cursor.execute('''
                    INSERT INTO configs (config_key, config_value, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (config[0], config[1], config[2], now, now))
            
            conn.commit()
        
        conn.close()
        logger.info("数据库初始化成功")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

def init_database():
    """数据库初始化的别名函数，用于兼容性"""
    return init_db()

def get_db_connection():
    """获取数据库连接"""
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 使查询结果可通过列名访问
        
        return conn
        
    except Exception as e:
        logger.error(f"获取数据库连接失败: {e}")
        raise

def execute_query(query, params=None):
    """执行查询并返回结果"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"执行查询失败: {e}")
        raise

def execute_update(query, params=None):
    """执行更新操作并返回影响的行数"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected_rows
        
    except Exception as e:
        logger.error(f"执行更新失败: {e}")
        raise

def insert_and_get_id(query, params=None):
    """执行插入操作并返回新插入行的ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return last_id
        
    except Exception as e:
        logger.error(f"执行插入失败: {e}")
        raise

def backup_database(backup_path=None):
    """备份数据库"""
    try:
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(__file__), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"video_pipeline_{timestamp}.db")
        
        # 连接源数据库
        source_conn = sqlite3.connect(DB_PATH)
        
        # 创建备份数据库
        backup_conn = sqlite3.connect(backup_path)
        
        # 执行备份
        source_conn.backup(backup_conn)
        
        # 关闭连接
        source_conn.close()
        backup_conn.close()
        
        logger.info(f"数据库备份成功: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        raise

# 测试代码
if __name__ == "__main__":
    print("=== 数据库管理模块测试 ===")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 初始化数据库
    init_db()
    
    # 测试连接
    conn = get_db_connection()
    print("数据库连接成功")
    
    # 查询用户
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print(f"用户数量: {len(users)}")
    
    # 关闭连接
    conn.close()
    
    print("数据库管理模块测试完成")