#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库脚本
解决任务表结构不匹配的问题
"""

import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database():
    """修复数据库表结构"""
    try:
        # 连接数据库
        db_path = 'tasks.db'
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            return False
        
        logger.info(f"连接数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查任务表结构
        cursor.execute('PRAGMA table_info(tasks)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info("当前任务表结构:")
        for col in columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
        # 检查是否需要修复
        needs_fix = False
        
        # 检查task_name列是否存在
        if 'task_name' not in column_names and 'name' in column_names:
            logger.info("需要添加task_name列作为name的别名")
            needs_fix = True
        
        # 检查task_type列是否存在
        if 'task_type' not in column_names and 'type' not in column_names:
            logger.info("需要添加task_type列")
            needs_fix = True
        
        # 执行修复
        if needs_fix:
            logger.info("开始修复数据库表结构...")
            
            # 创建临时表
            cursor.execute('''
                CREATE TABLE tasks_temp (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    completed_at TEXT,
                    config TEXT,
                    result TEXT,
                    error TEXT
                )
            ''')
            
            # 复制数据
            try:
                cursor.execute('''
                    INSERT INTO tasks_temp (id, name, task_name, task_type, status, progress, 
                                          created_at, updated_at, completed_at, config, result, error)
                    SELECT id, name, name, task_type, status, progress, 
                           created_time, created_time, completed_time, params, result, error_message
                    FROM tasks
                ''')
            except sqlite3.Error as e:
                logger.error(f"复制数据失败: {e}")
                # 尝试不同的列名
                try:
                    cursor.execute('''
                        INSERT INTO tasks_temp (id, name, task_name, task_type, status, progress, 
                                              created_at, updated_at, completed_at, config, result, error)
                        SELECT id, name, name, type, status, progress, 
                               created_time, created_time, completed_time, params, result, error_message
                        FROM tasks
                    ''')
                except sqlite3.Error as e2:
                    logger.error(f"第二次尝试复制数据失败: {e2}")
                    conn.rollback()
                    conn.close()
                    return False
            
            # 删除原表
            cursor.execute('DROP TABLE tasks')
            
            # 重命名临时表
            cursor.execute('ALTER TABLE tasks_temp RENAME TO tasks')
            
            # 提交更改
            conn.commit()
            logger.info("数据库表结构修复完成")
            
            # 检查修复后的表结构
            cursor.execute('PRAGMA table_info(tasks)')
            columns = cursor.fetchall()
            logger.info("修复后的任务表结构:")
            for col in columns:
                logger.info(f"  {col[1]} ({col[2]})")
        else:
            logger.info("数据库表结构无需修复")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"修复数据库失败: {e}")
        return False

if __name__ == "__main__":
    fix_database()