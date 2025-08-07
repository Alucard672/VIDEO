#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化数据库脚本
"""

import sqlite3
import os
from pathlib import Path

def init_database():
    """初始化数据库"""
    try:
        # 创建数据库
        db_path = 'tasks.db'
        print(f'创建数据库: {db_path}')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                priority INTEGER DEFAULT 2,
                params TEXT,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                result TEXT,
                error_message TEXT,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_time DATETIME,
                completed_time DATETIME,
                scheduled_time DATETIME,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                timeout INTEGER DEFAULT 3600,
                dependencies TEXT
            )
        ''')
        
        # 创建任务日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # 创建任务统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_stats (
                date TEXT PRIMARY KEY,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                avg_duration REAL DEFAULT 0,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print('数据库创建完成')
        print(f'数据库文件存在: {os.path.exists(db_path)}')
        
        # 检查表结构
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('PRAGMA table_info(tasks)')
        columns = cursor.fetchall()
        print('\n任务表结构:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        cursor.execute('SELECT COUNT(*) FROM tasks')
        count = cursor.fetchone()[0]
        print(f'\n任务总数: {count}')
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f'数据库初始化失败: {e}')
        return False

if __name__ == "__main__":
    init_database()