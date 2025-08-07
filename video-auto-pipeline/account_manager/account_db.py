#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号信息加密存储与管理模块
"""

import sqlite3
import json
import time
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
from config import DatabaseConfig

class AccountDatabase:
    """账号数据库管理器"""
    
    def __init__(self):
        self.db_path = DatabaseConfig.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成加密密钥
        self.key_file = Path("config/encryption_key.key")
        self.key_file.parent.mkdir(exist_ok=True)
        
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建账号表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        username TEXT NOT NULL,
                        encrypted_password TEXT NOT NULL,
                        encrypted_cookies TEXT,
                        encrypted_tokens TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        login_count INTEGER DEFAULT 0,
                        group_name TEXT DEFAULT 'default',
                        notes TEXT
                    )
                ''')
                
                # 创建登录日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS login_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        FOREIGN KEY (account_id) REFERENCES accounts (id)
                    )
                ''')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def _encrypt_data(self, data: str) -> str:
        """加密数据"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def add_account(self, platform: str, username: str, password: str, 
                   cookies: str = None, tokens: str = None, 
                   group_name: str = "default", notes: str = None) -> bool:
        """添加账号"""
        logger.info(f"添加账号: {platform} - {username}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查账号是否已存在
                cursor.execute(
                    "SELECT id FROM accounts WHERE platform = ? AND username = ?",
                    (platform, username)
                )
                
                if cursor.fetchone():
                    logger.warning(f"账号已存在: {platform} - {username}")
                    return False
                
                # 加密敏感数据
                encrypted_password = self._encrypt_data(password)
                encrypted_cookies = self._encrypt_data(cookies) if cookies else None
                encrypted_tokens = self._encrypt_data(tokens) if tokens else None
                
                # 插入账号数据
                cursor.execute('''
                    INSERT INTO accounts (platform, username, encrypted_password, 
                                       encrypted_cookies, encrypted_tokens, group_name, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (platform, username, encrypted_password, encrypted_cookies, 
                     encrypted_tokens, group_name, notes))
                
                conn.commit()
                logger.info(f"账号添加成功: {platform} - {username}")
                return True
                
        except Exception as e:
            logger.error(f"账号添加失败: {e}")
            return False
    
    def update_account(self, account_id: int, **kwargs) -> bool:
        """更新账号信息"""
        logger.info(f"更新账号: {account_id}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                update_fields = []
                update_values = []
                
                for key, value in kwargs.items():
                    if key in ['password', 'cookies', 'tokens']:
                        # 加密敏感数据
                        encrypted_value = self._encrypt_data(value)
                        update_fields.append(f"encrypted_{key} = ?")
                        update_values.append(encrypted_value)
                    elif key in ['username', 'platform', 'status', 'group_name', 'notes']:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                if not update_fields:
                    logger.warning("没有要更新的字段")
                    return False
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(account_id)
                
                query = f"UPDATE accounts SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                logger.info(f"账号更新成功: {account_id}")
                return True
                
        except Exception as e:
            logger.error(f"账号更新失败: {e}")
            return False
    
    def delete_account(self, account_id: int) -> bool:
        """删除账号"""
        logger.info(f"删除账号: {account_id}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"账号删除成功: {account_id}")
                    return True
                else:
                    logger.warning(f"账号不存在: {account_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"账号删除失败: {e}")
            return False
    
    def get_account(self, account_id: int) -> Optional[Dict]:
        """获取账号信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_dict(row)
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"获取账号失败: {e}")
            return None
    
    def get_accounts_by_platform(self, platform: str) -> List[Dict]:
        """根据平台获取账号列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM accounts WHERE platform = ?", (platform,))
                rows = cursor.fetchall()
                
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"获取平台账号失败: {e}")
            return []
    
    def get_active_accounts(self) -> List[Dict]:
        """获取所有活跃账号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM accounts WHERE status = 'active'")
                rows = cursor.fetchall()
                
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"获取活跃账号失败: {e}")
            return []
    
    def _row_to_dict(self, row) -> Dict:
        """将数据库行转换为字典"""
        columns = [
            'id', 'platform', 'username', 'encrypted_password', 
            'encrypted_cookies', 'encrypted_tokens', 'status', 
            'created_at', 'updated_at', 'last_login', 'login_count', 
            'group_name', 'notes'
        ]
        
        account_dict = dict(zip(columns, row))
        
        # 解密敏感数据
        if account_dict.get('encrypted_password'):
            account_dict['password'] = self._decrypt_data(account_dict['encrypted_password'])
        if account_dict.get('encrypted_cookies'):
            account_dict['cookies'] = self._decrypt_data(account_dict['encrypted_cookies'])
        if account_dict.get('encrypted_tokens'):
            account_dict['tokens'] = self._decrypt_data(account_dict['encrypted_tokens'])
        
        # 删除加密字段
        for key in ['encrypted_password', 'encrypted_cookies', 'encrypted_tokens']:
            account_dict.pop(key, None)
        
        return account_dict
    
    def add_login_log(self, account_id: int, status: str, 
                     ip_address: str = None, user_agent: str = None):
        """添加登录日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO login_logs (account_id, status, ip_address, user_agent)
                    VALUES (?, ?, ?, ?)
                ''', (account_id, status, ip_address, user_agent))
                
                # 更新账号登录信息
                cursor.execute('''
                    UPDATE accounts 
                    SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                    WHERE id = ?
                ''', (account_id,))
                
                conn.commit()
                logger.info(f"登录日志添加成功: {account_id}")
                
        except Exception as e:
            logger.error(f"登录日志添加失败: {e}")
    
    def get_login_logs(self, account_id: int = None, limit: int = 100) -> List[Dict]:
        """获取登录日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if account_id:
                    cursor.execute('''
                        SELECT * FROM login_logs 
                        WHERE account_id = ? 
                        ORDER BY login_time DESC 
                        LIMIT ?
                    ''', (account_id, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM login_logs 
                        ORDER BY login_time DESC 
                        LIMIT ?
                    ''', (limit,))
                
                rows = cursor.fetchall()
                
                columns = ['id', 'account_id', 'login_time', 'status', 'ip_address', 'user_agent']
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"获取登录日志失败: {e}")
            return []

def main():
    """主函数"""
    db = AccountDatabase()
    
    # 示例：添加账号
    success = db.add_account(
        platform="douyin",
        username="test_user",
        password="test_password",
        cookies="test_cookies",
        group_name="test_group",
        notes="测试账号"
    )
    
    if success:
        logger.info("账号添加成功")
        
        # 获取账号列表
        accounts = db.get_accounts_by_platform("douyin")
        logger.info(f"获取到 {len(accounts)} 个抖音账号")
        
        # 添加登录日志
        if accounts:
            db.add_login_log(accounts[0]['id'], "success", "127.0.0.1", "test_agent")
    
    logger.info("账号数据库管理完成")

if __name__ == "__main__":
    main() 