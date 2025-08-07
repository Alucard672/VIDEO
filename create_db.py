#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建数据库脚本
"""

import sqlite3
import os
from pathlib import Path

def create_database():
    """创建数据库"""
    try:
        # 创建数据库
        db_path = 'tasks.db'
        print(f'在当前目录创建数据库: {db_path}')
        
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
        
        conn.commit()
        conn.close()
        
        print('数据库创建成功')
        print(f'数据库文件存在: {os.path.exists(db_path)}')
        
        # 验证数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks')
        count = cursor.fetchone()[0]
        print(f'任务总数: {count}')
        conn.close()
        
        return True
        
    except Exception as e:
        print(f'创建数据库失败: {e}')
        return False

if __name__ == "__main__":
    create_database()