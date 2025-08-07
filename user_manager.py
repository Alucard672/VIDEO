#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理器
负责用户认证、权限管理和会话管理
"""

import os
import sys
import json
import sqlite3
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
import bcrypt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from config import DATABASE_PATH, security_config
    from config.environment import get_config
except ImportError:
    DATABASE_PATH = project_root / "data" / "users.db"
    
    class MockConfig:
        SECRET_KEY = 'dev-secret-key'
        JWT_SECRET_KEY = 'dev-jwt-secret-key'
        SESSION_TIMEOUT = 3600
    
    security_config = MockConfig()

class UserRole:
    """用户角色"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    OPERATOR = "operator"

class Permission:
    """权限定义"""
    # 系统管理权限
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    
    # 任务管理权限
    TASK_CREATE = "task:create"
    TASK_VIEW = "task:view"
    TASK_EDIT = "task:edit"
    TASK_DELETE = "task:delete"
    TASK_EXECUTE = "task:execute"
    
    # 视频管理权限
    VIDEO_UPLOAD = "video:upload"
    VIDEO_VIEW = "video:view"
    VIDEO_EDIT = "video:edit"
    VIDEO_DELETE = "video:delete"
    VIDEO_PUBLISH = "video:publish"
    
    # 账号管理权限
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_VIEW = "account:view"
    ACCOUNT_EDIT = "account:edit"
    ACCOUNT_DELETE = "account:delete"
    
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_VIEW = "user:view"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    
    # 数据分析权限
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"

class User:
    """用户类"""
    
    def __init__(self, user_id: int, username: str, email: str, 
                 role: str, permissions: List[str] = None,
                 created_time: datetime = None, last_login: datetime = None,
                 is_active: bool = True):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.permissions = permissions or []
        self.created_time = created_time or datetime.now()
        self.last_login = last_login
        self.is_active = is_active
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions or self.role == UserRole.ADMIN
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'permissions': self.permissions,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH.parent / "users.db"
        self.secret_key = security_config.SECRET_KEY
        self.jwt_secret = security_config.JWT_SECRET_KEY
        self.session_timeout = security_config.SESSION_TIMEOUT
        
        # 角色权限映射
        self.role_permissions = {
            UserRole.ADMIN: [
                Permission.SYSTEM_ADMIN, Permission.SYSTEM_CONFIG, Permission.SYSTEM_MONITOR,
                Permission.TASK_CREATE, Permission.TASK_VIEW, Permission.TASK_EDIT, 
                Permission.TASK_DELETE, Permission.TASK_EXECUTE,
                Permission.VIDEO_UPLOAD, Permission.VIDEO_VIEW, Permission.VIDEO_EDIT,
                Permission.VIDEO_DELETE, Permission.VIDEO_PUBLISH,
                Permission.ACCOUNT_CREATE, Permission.ACCOUNT_VIEW, Permission.ACCOUNT_EDIT,
                Permission.ACCOUNT_DELETE,
                Permission.USER_CREATE, Permission.USER_VIEW, Permission.USER_EDIT,
                Permission.USER_DELETE,
                Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT
            ],
            UserRole.OPERATOR: [
                Permission.TASK_CREATE, Permission.TASK_VIEW, Permission.TASK_EDIT,
                Permission.TASK_EXECUTE,
                Permission.VIDEO_UPLOAD, Permission.VIDEO_VIEW, Permission.VIDEO_EDIT,
                Permission.VIDEO_PUBLISH,
                Permission.ACCOUNT_VIEW, Permission.ACCOUNT_EDIT,
                Permission.ANALYTICS_VIEW
            ],
            UserRole.USER: [
                Permission.TASK_VIEW, Permission.TASK_CREATE,
                Permission.VIDEO_VIEW, Permission.VIDEO_UPLOAD,
                Permission.ACCOUNT_VIEW,
                Permission.ANALYTICS_VIEW
            ],
            UserRole.VIEWER: [
                Permission.TASK_VIEW,
                Permission.VIDEO_VIEW,
                Permission.ACCOUNT_VIEW,
                Permission.ANALYTICS_VIEW
            ]
        }
        
        # 初始化数据库
        self._init_database()
        
        # 创建默认管理员账户
        self._create_default_admin()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    permissions TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until DATETIME
                )
            ''')
            
            # 创建会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_time DATETIME NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 创建用户操作日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("用户管理数据库初始化完成")
            
        except Exception as e:
            logger.error(f"用户管理数据库初始化失败: {e}")
            raise
    
    def _create_default_admin(self):
        """创建默认管理员账户"""
        try:
            # 检查是否已存在管理员账户
            if self.get_user_by_username('admin'):
                return
            
            # 创建默认管理员
            result = self.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role=UserRole.ADMIN
            )
            
            if result['success']:
                logger.info("默认管理员账户创建成功: admin / admin123")
            else:
                logger.warning(f"默认管理员账户创建失败: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"创建默认管理员账户失败: {e}")
    
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """密码哈希"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # 使用bcrypt进行密码哈希
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # 组合密码和盐
        combined = password_bytes + salt_bytes
        
        # 使用bcrypt哈希
        hashed = bcrypt.hashpw(combined, bcrypt.gensalt())
        
        return hashed.decode('utf-8'), salt
    
    def _verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """验证密码"""
        try:
            password_bytes = password.encode('utf-8')
            salt_bytes = salt.encode('utf-8')
            combined = password_bytes + salt_bytes
            
            return bcrypt.checkpw(combined, hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False
    
    def create_user(self, username: str, email: str, password: str, 
                   role: str = UserRole.USER) -> Dict[str, Any]:
        """创建用户"""
        try:
            # 验证输入
            if not username or not email or not password:
                return {'success': False, 'error': '用户名、邮箱和密码不能为空'}
            
            if len(password) < 6:
                return {'success': False, 'error': '密码长度至少6位'}
            
            # 检查用户名和邮箱是否已存在
            if self.get_user_by_username(username):
                return {'success': False, 'error': '用户名已存在'}
            
            if self.get_user_by_email(email):
                return {'success': False, 'error': '邮箱已存在'}
            
            # 哈希密码
            password_hash, salt = self._hash_password(password)
            
            # 获取角色权限
            permissions = self.role_permissions.get(role, [])
            
            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, role, permissions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, role, json.dumps(permissions)))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # 记录日志
            self.log_user_action(user_id, 'user_created', f'用户 {username} 创建成功')
            
            logger.info(f"用户创建成功: {username} ({user_id})")
            
            return {
                'success': True,
                'user_id': user_id,
                'message': '用户创建成功'
            }
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """用户认证"""
        try:
            # 获取用户信息
            user = self.get_user_by_username(username)
            if not user:
                self.log_user_action(None, 'login_failed', f'用户名不存在: {username}', ip_address, user_agent)
                return {'success': False, 'error': '用户名或密码错误'}
            
            # 检查账户是否被锁定
            if user.get('locked_until'):
                locked_until = datetime.fromisoformat(user['locked_until'])
                if datetime.now() < locked_until:
                    return {'success': False, 'error': '账户已被锁定，请稍后再试'}
            
            # 检查账户是否激活
            if not user.get('is_active', True):
                return {'success': False, 'error': '账户已被禁用'}
            
            # 验证密码
            if not self._verify_password(password, user['password_hash'], user['salt']):
                # 增加登录失败次数
                self._increment_login_attempts(user['id'])
                self.log_user_action(user['id'], 'login_failed', '密码错误', ip_address, user_agent)
                return {'success': False, 'error': '用户名或密码错误'}
            
            # 重置登录失败次数
            self._reset_login_attempts(user['id'])
            
            # 更新最后登录时间
            self._update_last_login(user['id'])
            
            # 创建会话
            session_token = self._create_session(user['id'], ip_address, user_agent)
            
            # 生成JWT令牌
            jwt_token = self._generate_jwt_token(user)
            
            # 记录登录日志
            self.log_user_action(user['id'], 'login_success', '登录成功', ip_address, user_agent)
            
            logger.info(f"用户登录成功: {username} ({user['id']})")
            
            return {
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'permissions': json.loads(user.get('permissions', '[]'))
                },
                'session_token': session_token,
                'jwt_token': jwt_token,
                'expires_in': self.session_timeout
            }
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return {'success': False, 'error': '认证失败'}
    
    def _increment_login_attempts(self, user_id: int):
        """增加登录失败次数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET login_attempts = login_attempts + 1,
                    locked_until = CASE 
                        WHEN login_attempts >= 4 THEN datetime('now', '+30 minutes')
                        ELSE locked_until
                    END
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新登录失败次数失败: {e}")
    
    def _reset_login_attempts(self, user_id: int):
        """重置登录失败次数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET login_attempts = 0, locked_until = NULL
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"重置登录失败次数失败: {e}")
    
    def _update_last_login(self, user_id: int):
        """更新最后登录时间"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {e}")
    
    def _create_session(self, user_id: int, ip_address: str = None, 
                       user_agent: str = None) -> str:
        """创建用户会话"""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_time = datetime.now() + timedelta(seconds=self.session_timeout)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (user_id, session_token, expires_time, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_time, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            logger.error(f"创建用户会话失败: {e}")
            return None
    
    def _generate_jwt_token(self, user: Dict[str, Any]) -> str:
        """生成JWT令牌"""
        try:
            payload = {
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token
            
        except Exception as e:
            logger.error(f"生成JWT令牌失败: {e}")
            return None
    
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, s.expires_time, u.username, u.email, u.role, u.permissions, u.is_active
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.is_active = TRUE
            ''', (session_token,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # 检查会话是否过期
            expires_time = datetime.fromisoformat(row[1])
            if datetime.now() > expires_time:
                self._deactivate_session(session_token)
                return None
            
            # 检查用户是否激活
            if not row[6]:
                return None
            
            return {
                'user_id': row[0],
                'username': row[2],
                'email': row[3],
                'role': row[4],
                'permissions': json.loads(row[5] or '[]'),
                'is_active': row[6]
            }
            
        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return None
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # 获取用户信息
            user = self.get_user_by_id(payload['user_id'])
            if not user or not user.get('is_active', True):
                return None
            
            return {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role']
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的JWT令牌: {e}")
            return None
        except Exception as e:
            logger.error(f"验证JWT令牌失败: {e}")
            return None
    
    def _deactivate_session(self, session_token: str):
        """停用会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE
                WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"停用会话失败: {e}")
    
    def logout_user(self, session_token: str) -> Dict[str, Any]:
        """用户登出"""
        try:
            # 获取会话信息
            session_info = self.verify_session(session_token)
            if session_info:
                self.log_user_action(session_info['user_id'], 'logout', '用户登出')
            
            # 停用会话
            self._deactivate_session(session_token)
            
            return {'success': True, 'message': '登出成功'}
            
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, role, permissions, 
                       is_active, created_time, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'password_hash': row[3],
                    'salt': row[4],
                    'role': row[5],
                    'permissions': row[6],
                    'is_active': row[7],
                    'created_time': row[8],
                    'last_login': row[9]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, role, permissions, 
                       is_active, created_time, last_login
                FROM users WHERE username = ?
            ''', (username,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'password_hash': row[3],
                    'salt': row[4],
                    'role': row[5],
                    'permissions': row[6],
                    'is_active': row[7],
                    'created_time': row[8],
                    'last_login': row[9]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, role, permissions, 
                       is_active, created_time, last_login
                FROM users WHERE email = ?
            ''', (email,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'password_hash': row[3],
                    'salt': row[4],
                    'role': row[5],
                    'permissions': row[6],
                    'is_active': row[7],
                    'created_time': row[8],
                    'last_login': row[9]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户（用于兼容性）"""
        # 这是一个简化的实现，实际应该从会话中获取
        return {
            'username': '管理员',
            'role': 'admin',
            'email': 'admin@example.com'
        }
    
    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """获取所有用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, username, email, role, is_active, created_time, last_login
                FROM users
            '''
            
            if not include_inactive:
                query += ' WHERE is_active = TRUE'
            
            query += ' ORDER BY created_time DESC'
            
            cursor.execute(query)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3],
                    'is_active': row[4],
                    'created_time': row[5],
                    'last_login': row[6]
                })
            
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            return []
    
    def update_user(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息"""
        try:
            # 检查用户是否存在
            user = self.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 构建更新语句
            update_fields = []
            update_values = []
            
            if 'username' in updates:
                # 检查用户名是否已存在
                existing_user = self.get_user_by_username(updates['username'])
                if existing_user and existing_user['id'] != user_id:
                    return {'success': False, 'error': '用户名已存在'}
                update_fields.append('username = ?')
                update_values.append(updates['username'])
            
            if 'email' in updates:
                # 检查邮箱是否已存在
                existing_user = self.get_user_by_email(updates['email'])
                if existing_user and existing_user['id'] != user_id:
                    return {'success': False, 'error': '邮箱已存在'}
                update_fields.append('email = ?')
                update_values.append(updates['email'])
            
            if 'role' in updates:
                update_fields.append('role = ?')
                update_values.append(updates['role'])
                
                # 更新权限
                permissions = self.role_permissions.get(updates['role'], [])
                update_fields.append('permissions = ?')
                update_values.append(json.dumps(permissions))
            
            if 'is_active' in updates:
                update_fields.append('is_active = ?')
                update_values.append(updates['is_active'])
            
            if 'password' in updates:
                password_hash, salt = self._hash_password(updates['password'])
                update_fields.append('password_hash = ?')
                update_fields.append('salt = ?')
                update_values.extend([password_hash, salt])
            
            if not update_fields:
                return {'success': False, 'error': '没有要更新的字段'}
            
            # 执行更新
            update_values.append(user_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = ?
            ''', update_values)
            
            conn.commit()
            conn.close()
            
            # 记录日志
            self.log_user_action(user_id, 'user_updated', f'用户信息更新: {list(updates.keys())}')
            
            logger.info(f"用户更新成功: {user['username']} ({user_id})")
            
            return {'success': True, 'message': '用户更新成功'}
            
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """删除用户"""
        try:
            # 检查用户是否存在
            user = self.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 不能删除管理员账户
            if user['role'] == UserRole.ADMIN:
                return {'success': False, 'error': '不能删除管理员账户'}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除用户
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            # 删除相关会话
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            # 记录日志
            self.log_user_action(user_id, 'user_deleted', f'用户 {user["username"]} 被删除')
            
            logger.info(f"用户删除成功: {user['username']} ({user_id})")
            
            return {'success': True, 'message': '用户删除成功'}
            
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改密码"""
        try:
            # 获取用户信息
            user = self.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 验证旧密码
            if not self._verify_password(old_password, user['password_hash'], user['salt']):
                return {'success': False, 'error': '原密码错误'}
            
            # 验证新密码
            if len(new_password) < 6:
                return {'success': False, 'error': '新密码长度至少6位'}
            
            # 哈希新密码
            password_hash, salt = self._hash_password(new_password)
            
            # 更新密码
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, salt = ?
                WHERE id = ?
            ''', (password_hash, salt, user_id))
            
            conn.commit()
            conn.close()
            
            # 记录日志
            self.log_user_action(user_id, 'password_changed', '密码修改成功')
            
            logger.info(f"用户密码修改成功: {user['username']} ({user_id})")
            
            return {'success': True, 'message': '密码修改成功'}
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def reset_password(self, user_id: int, new_password: str) -> Dict[str, Any]:
        """重置密码（管理员操作）"""
        try:
            # 获取用户信息
            user = self.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 验证新密码
            if len(new_password) < 6:
                return {'success': False, 'error': '新密码长度至少6位'}
            
            # 哈希新密码
            password_hash, salt = self._hash_password(new_password)
            
            # 更新密码
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, salt = ?, login_attempts = 0, locked_until = NULL
                WHERE id = ?
            ''', (password_hash, salt, user_id))
            
            conn.commit()
            conn.close()
            
            # 记录日志
            self.log_user_action(user_id, 'password_reset', '密码被管理员重置')
            
            logger.info(f"用户密码重置成功: {user['username']} ({user_id})")
            
            return {'success': True, 'message': '密码重置成功'}
            
        except Exception as e:
            logger.error(f"重置密码失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_permission(self, user_id: int, permission: str) -> bool:
        """检查用户权限"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 管理员拥有所有权限
            if user['role'] == UserRole.ADMIN:
                return True
            
            # 检查用户权限
            permissions = json.loads(user.get('permissions', '[]'))
            return permission in permissions
            
        except Exception as e:
            logger.error(f"检查用户权限失败: {e}")
            return False
    
    def log_user_action(self, user_id: Optional[int], action: str, details: str = None,
                       ip_address: str = None, user_agent: str = None):
        """记录用户操作日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_logs (user_id, action, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action, details, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"记录用户操作日志失败: {e}")
    
    def get_user_logs(self, user_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户操作日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT l.action, l.details, l.ip_address, l.user_agent, l.timestamp, u.username
                    FROM user_logs l
                    LEFT JOIN users u ON l.user_id = u.id
                    WHERE l.user_id = ?
                    ORDER BY l.timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT l.action, l.details, l.ip_address, l.user_agent, l.timestamp, u.username
                    FROM user_logs l
                    LEFT JOIN users u ON l.user_id = u.id
                    ORDER BY l.timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'action': row[0],
                    'details': row[1],
                    'ip_address': row[2],
                    'user_agent': row[3],
                    'timestamp': row[4],
                    'username': row[5] or '系统'
                })
            
            conn.close()
            return logs
            
        except Exception as e:
            logger.error(f"获取用户操作日志失败: {e}")
            return []
    
    def get_active_sessions(self, user_id: int = None) -> List[Dict[str, Any]]:
        """获取活跃会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT s.session_token, s.created_time, s.expires_time, s.ip_address, 
                           s.user_agent, u.username
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.user_id = ? AND s.is_active = TRUE AND s.expires_time > datetime('now')
                    ORDER BY s.created_time DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT s.session_token, s.created_time, s.expires_time, s.ip_address, 
                           s.user_agent, u.username
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.is_active = TRUE AND s.expires_time > datetime('now')
                    ORDER BY s.created_time DESC
                ''')
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_token': row[0],
                    'created_time': row[1],
                    'expires_time': row[2],
                    'ip_address': row[3],
                    'user_agent': row[4],
                    'username': row[5]
                })
            
            conn.close()
            return sessions
            
        except Exception as e:
            logger.error(f"获取活跃会话失败: {e}")
            return []
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE
                WHERE expires_time <= datetime('now')
            ''')
            
            cleaned_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个过期会话")
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 用户总数
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
            total_users = cursor.fetchone()[0]
            
            # 角色分布
            cursor.execute('''
                SELECT role, COUNT(*) 
                FROM users 
                WHERE is_active = TRUE 
                GROUP BY role
            ''')
            role_distribution = dict(cursor.fetchall())
            
            # 今日登录用户数
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM user_sessions 
                WHERE DATE(created_time) = DATE('now')
            ''')
            today_logins = cursor.fetchone()[0]
            
            # 活跃会话数
            cursor.execute('''
                SELECT COUNT(*) 
                FROM user_sessions 
                WHERE is_active = TRUE AND expires_time > datetime('now')
            ''')
            active_sessions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'role_distribution': role_distribution,
                'today_logins': today_logins,
                'active_sessions': active_sessions
            }
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return {
                'total_users': 0,
                'role_distribution': {},
                'today_logins': 0,
                'active_sessions': 0
            }

def main():
    """测试函数"""
    user_manager = UserManager()
    
    print("=== 用户管理器测试 ===")
    
    # 创建测试用户
    result = user_manager.create_user(
        username='testuser',
        email='test@example.com',
        password='test123',
        role=UserRole.USER
    )
    print(f"创建用户结果: {result}")
    
    # 用户认证
    auth_result = user_manager.authenticate_user('testuser', 'test123')
    print(f"用户认证结果: {auth_result['success']}")
    
    # 获取用户统计
    stats = user_manager.get_user_statistics()
    print(f"用户统计: {stats}")
    
    # 获取所有用户
    users = user_manager.get_all_users()
    print(f"用户总数: {len(users)}")
    
    print("用户管理器测试完成")

if __name__ == "__main__":
    main()
