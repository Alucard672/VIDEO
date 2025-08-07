#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理模块
提供用户管理、认证和授权功能
"""

import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

class UserManager:
    """用户管理类"""
    
    def __init__(self):
        """初始化用户管理器"""
        self.active_sessions = {}  # 存储活跃会话
        self.session_timeout = 3600  # 会话超时时间（秒）
        logger.info("用户管理器初始化完成")
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """验证用户身份
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (认证是否成功, 用户信息)
        """
        try:
            # 从数据库获取用户
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, password, email, role, status FROM users WHERE username = ?",
                (username,)
            )
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                logger.warning(f"用户不存在: {username}")
                return False, None
            
            # 检查用户状态
            if user['status'] != 'active':
                logger.warning(f"用户状态非活跃: {username}")
                return False, None
            
            # 验证密码
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            if hashed_password != user['password']:
                logger.warning(f"密码错误: {username}")
                return False, None
            
            # 更新最后登录时间
            self._update_last_login(user['id'])
            
            # 返回用户信息
            user_info = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
            
            logger.info(f"用户认证成功: {username}")
            return True, user_info
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return False, None
    
    def create_user(self, username: str, password: str, email: str = None, role: str = 'user') -> Tuple[bool, Optional[int]]:
        """创建新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 电子邮件
            role: 角色
            
        Returns:
            (创建是否成功, 用户ID)
        """
        try:
            # 检查用户名是否已存在
            if self._user_exists(username):
                logger.warning(f"用户名已存在: {username}")
                return False, None
            
            # 检查邮箱是否已存在
            if email and self._email_exists(email):
                logger.warning(f"邮箱已存在: {email}")
                return False, None
            
            # 哈希密码
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # 插入用户
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO users (username, password, email, role, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (username, hashed_password, email, role, datetime.now().isoformat(), 'active')
            )
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"用户创建成功: {username}")
            return True, user_id
            
        except Exception as e:
            logger.error(f"用户创建失败: {e}")
            return False, None
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            data: 要更新的数据
            
        Returns:
            是否更新成功
        """
        try:
            # 检查用户是否存在
            if not self._user_id_exists(user_id):
                logger.warning(f"用户ID不存在: {user_id}")
                return False
            
            # 准备更新字段
            update_fields = []
            params = []
            
            if 'email' in data:
                update_fields.append("email = ?")
                params.append(data['email'])
            
            if 'role' in data:
                update_fields.append("role = ?")
                params.append(data['role'])
            
            if 'status' in data:
                update_fields.append("status = ?")
                params.append(data['status'])
            
            if 'password' in data:
                hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
                update_fields.append("password = ?")
                params.append(hashed_password)
            
            if not update_fields:
                logger.warning("没有要更新的字段")
                return False
            
            # 添加更新时间
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            # 添加用户ID
            params.append(user_id)
            
            # 执行更新
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户更新成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"用户更新失败: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            # 检查用户是否存在
            if not self._user_id_exists(user_id):
                logger.warning(f"用户ID不存在: {user_id}")
                return False
            
            # 执行删除
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户删除成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"用户删除失败: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, email, role, created_at, last_login, status FROM users WHERE id = ?",
                (user_id,)
            )
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                logger.warning(f"用户ID不存在: {user_id}")
                return None
            
            return dict(user)
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户
        
        Returns:
            用户列表
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, email, role, created_at, last_login, status FROM users"
            )
            
            users = [dict(user) for user in cursor.fetchall()]
            conn.close()
            
            return users
            
        except Exception as e:
            logger.error(f"获取所有用户失败: {e}")
            return []
    
    def create_session(self, user_id: int) -> Optional[str]:
        """创建用户会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            会话令牌
        """
        try:
            # 生成会话令牌
            token = secrets.token_hex(32)
            
            # 存储会话
            self.active_sessions[token] = {
                'user_id': user_id,
                'created_at': time.time(),
                'expires_at': time.time() + self.session_timeout
            }
            
            return token
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None
    
    def validate_session(self, token: str) -> Tuple[bool, Optional[int]]:
        """验证会话
        
        Args:
            token: 会话令牌
            
        Returns:
            (会话是否有效, 用户ID)
        """
        try:
            if token not in self.active_sessions:
                return False, None
            
            session = self.active_sessions[token]
            
            # 检查会话是否过期
            if time.time() > session['expires_at']:
                del self.active_sessions[token]
                return False, None
            
            # 更新过期时间
            session['expires_at'] = time.time() + self.session_timeout
            
            return True, session['user_id']
            
        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return False, None
    
    def end_session(self, token: str) -> bool:
        """结束会话
        
        Args:
            token: 会话令牌
            
        Returns:
            是否成功结束会话
        """
        try:
            if token in self.active_sessions:
                del self.active_sessions[token]
                return True
            return False
            
        except Exception as e:
            logger.error(f"结束会话失败: {e}")
            return False
    
    def clean_expired_sessions(self) -> int:
        """清理过期会话
        
        Returns:
            清理的会话数量
        """
        try:
            expired_tokens = []
            
            for token, session in self.active_sessions.items():
                if time.time() > session['expires_at']:
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                del self.active_sessions[token]
            
            return len(expired_tokens)
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            是否修改成功
        """
        try:
            # 验证旧密码
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                logger.warning(f"用户ID不存在: {user_id}")
                return False
            
            hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()
            
            if hashed_old_password != user['password']:
                conn.close()
                logger.warning(f"旧密码错误: {user_id}")
                return False
            
            # 更新密码
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
            
            cursor.execute(
                "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                (hashed_new_password, datetime.now().isoformat(), user_id)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"密码修改成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"密码修改失败: {e}")
            return False
    
    def reset_password(self, user_id: int) -> Optional[str]:
        """重置密码
        
        Args:
            user_id: 用户ID
            
        Returns:
            新密码
        """
        try:
            # 生成随机密码
            new_password = secrets.token_hex(8)
            
            # 哈希密码
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            
            # 更新密码
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                (hashed_password, datetime.now().isoformat(), user_id)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"密码重置成功: {user_id}")
            return new_password
            
        except Exception as e:
            logger.error(f"密码重置失败: {e}")
            return None
    
    def get_user_count(self) -> int:
        """获取用户数量
        
        Returns:
            用户数量
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"获取用户数量失败: {e}")
            return 0
    
    def _user_exists(self, username: str) -> bool:
        """检查用户名是否存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"检查用户名是否存在失败: {e}")
            return False
    
    def _email_exists(self, email: str) -> bool:
        """检查邮箱是否存在
        
        Args:
            email: 电子邮件
            
        Returns:
            是否存在
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"检查邮箱是否存在失败: {e}")
            return False
    
    def _user_id_exists(self, user_id: int) -> bool:
        """检查用户ID是否存在
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否存在
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"检查用户ID是否存在失败: {e}")
            return False
    
    def _update_last_login(self, user_id: int) -> bool:
        """更新最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否更新成功
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    print("=== 用户管理模块测试 ===")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建用户管理器
    user_manager = UserManager()
    
    # 测试创建用户
    success, user_id = user_manager.create_user("testuser", "password123", "test@example.com")
    if success:
        print(f"用户创建成功，ID: {user_id}")
    else:
        print("用户创建失败")
    
    # 测试认证
    success, user_info = user_manager.authenticate("testuser", "password123")
    if success:
        print(f"认证成功: {user_info}")
    else:
        print("认证失败")
    
    # 测试获取用户
    user = user_manager.get_user(user_id)
    if user:
        print(f"获取用户成功: {user}")
    else:
        print("获取用户失败")
    
    # 测试修改密码
    if user_manager.change_password(user_id, "password123", "newpassword"):
        print("密码修改成功")
    else:
        print("密码修改失败")
    
    # 测试删除用户
    if user_manager.delete_user(user_id):
        print("用户删除成功")
    else:
        print("用户删除失败")
    
    print("用户管理模块测试完成")