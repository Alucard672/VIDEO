#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器
负责管理系统中的所有任务，包括创建、执行、监控和调度
"""

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
import uuid
import queue
import concurrent.futures

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from config import DATABASE_PATH, scheduler_config
    from config.environment import get_config
except ImportError:
    DATABASE_PATH = project_root / "data" / "tasks.db"
    
    class MockConfig:
        ENABLED = True
        MAX_CONCURRENT_TASKS = 5
        TASK_TIMEOUT = 3600
        RETRY_ATTEMPTS = 3
    
    scheduler_config = MockConfig()

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Task:
    """任务类"""
    
    def __init__(self, task_id: str, name: str, task_type: str, 
                 priority: TaskPriority = TaskPriority.NORMAL,
                 params: Dict[str, Any] = None,
                 scheduled_time: Optional[datetime] = None):
        self.id = task_id
        self.name = name
        self.task_type = task_type
        self.priority = priority
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error_message = None
        self.created_time = datetime.now()
        self.started_time = None
        self.completed_time = None
        self.scheduled_time = scheduled_time
        self.retry_count = 0
        self.max_retries = scheduler_config.RETRY_ATTEMPTS
        self.timeout = scheduler_config.TASK_TIMEOUT
        self.dependencies = []
        self.callback = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'priority': self.priority.value,
            'params': self.params,
            'status': self.status.value,
            'status_text': self.get_status_text(),
            'progress': self.progress,
            'result': self.result,
            'error_message': self.error_message,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'started_time': self.started_time.isoformat() if self.started_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'duration': self.get_duration()
        }
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        status_map = {
            TaskStatus.PENDING: '等待中',
            TaskStatus.RUNNING: '运行中',
            TaskStatus.COMPLETED: '已完成',
            TaskStatus.FAILED: '失败',
            TaskStatus.CANCELLED: '已取消',
            TaskStatus.PAUSED: '已暂停',
            TaskStatus.RETRYING: '重试中'
        }
        return status_map.get(self.status, '未知')
    
    def get_duration(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if self.started_time:
            end_time = self.completed_time or datetime.now()
            return (end_time - self.started_time).total_seconds()
        return None

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        # 确保使用当前目录的数据库路径
        self.db_path = Path(__file__).parent / "tasks.db"
        self.tasks = {}  # 内存中的任务缓存
        self.task_queue = queue.PriorityQueue()
        self.running_tasks = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=scheduler_config.MAX_CONCURRENT_TASKS
        )
        self.is_running = False
        self.scheduler_thread = None
        
        # 任务处理器注册表
        self.task_handlers = {}
        
        # 初始化数据库
        self._init_database()
        
        # 注册默认任务处理器
        self._register_default_handlers()
        
        # 启动任务调度器
        if scheduler_config.ENABLED:
            self.start_scheduler()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
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
            
            logger.info("任务管理数据库初始化完成")
            
        except Exception as e:
            logger.error(f"任务管理数据库初始化失败: {e}")
            raise
    
    def _register_default_handlers(self):
        """注册默认任务处理器"""
        self.register_handler('content_fetch', self._handle_content_fetch)
        self.register_handler('script_generation', self._handle_script_generation)
        self.register_handler('tts_generation', self._handle_tts_generation)
        self.register_handler('video_editing', self._handle_video_editing)
        self.register_handler('thumbnail_generation', self._handle_thumbnail_generation)
        self.register_handler('video_upload', self._handle_video_upload)
        self.register_handler('content_review', self._handle_content_review)
        self.register_handler('data_analysis', self._handle_data_analysis)
        self.register_handler('system_maintenance', self._handle_system_maintenance)
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"已注册任务处理器: {task_type}")
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        try:
            # 验证必需字段
            if not task_data.get('name'):
                return {
                    'error': '任务名称不能为空',
                    'status': 'failed'
                }
            
            if not task_data.get('task_type'):
                return {
                    'error': '任务类型不能为空',
                    'status': 'failed'
                }
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 解析优先级
            priority_value = int(task_data.get('priority', 2))
            if priority_value not in [1, 2, 3, 4]:
                priority_value = 2
            priority = TaskPriority(priority_value)
            
            # 解析计划时间
            scheduled_time = None
            if task_data.get('scheduled_time'):
                try:
                    scheduled_time = datetime.fromisoformat(task_data['scheduled_time'].replace('T', ' '))
                except ValueError:
                    # 如果时间格式不正确，忽略计划时间
                    pass
            
            # 创建任务对象
            task = Task(
                task_id=task_id,
                name=str(task_data['name']),
                task_type=str(task_data['task_type']),
                priority=priority,
                params=task_data.get('params', {}),
                scheduled_time=scheduled_time
            )
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 添加到内存缓存
            self.tasks[task_id] = task
            
            logger.info(f"任务已保存到数据库和内存缓存: {task_id}")
            
            # 添加到任务队列
            if not scheduled_time or scheduled_time <= datetime.now():
                self.task_queue.put((priority.value * -1, task_id))  # 负值用于优先级排序
            
            logger.info(f"任务创建成功: {task.name} ({task_id})")
            
            return {
                'id': task_id,
                'status': 'created',
                'message': '任务创建成功',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'success': False
            }
    
    def _save_task_to_db(self, task: Task):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, name, task_type, priority, params, status, progress, 
                 result, error_message, created_time, started_time, completed_time,
                 scheduled_time, retry_count, max_retries, timeout, dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.name, task.task_type, task.priority.value,
                json.dumps(task.params), task.status.value, task.progress,
                json.dumps(task.result) if task.result else None,
                task.error_message,
                task.created_time, task.started_time, task.completed_time,
                task.scheduled_time, task.retry_count, task.max_retries,
                task.timeout, json.dumps(task.dependencies)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        try:
            # 先从内存缓存获取
            if task_id in self.tasks:
                return self.tasks[task_id].to_dict()
            
            # 从数据库获取
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_task_dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def get_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的任务"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM tasks 
                ORDER BY created_time DESC 
                LIMIT ?
            ''', (limit,))
            
            tasks = []
            rows = cursor.fetchall()
            logger.info(f"从数据库获取到 {len(rows)} 个任务")
            
            for row in rows:
                task_dict = self._row_to_task_dict(row)
                tasks.append(task_dict)
                logger.debug(f"任务: {task_dict.get('name')} - {task_dict.get('id')}")
            
            conn.close()
            logger.info(f"返回任务列表，共 {len(tasks)} 个任务")
            return tasks
            
        except Exception as e:
            logger.error(f"获取最近任务失败: {e}")
            return []
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 今日任务统计
            today = datetime.now().date()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_tasks
                FROM tasks 
                WHERE DATE(created_time) = ?
            ''', (today,))
            
            row = cursor.fetchone()
            
            stats = {
                'today_tasks': row[0] or 0,
                'completed_tasks': row[1] or 0,
                'failed_tasks': row[2] or 0,
                'running_tasks': row[3] or 0,
                'today_videos': 0  # 需要从视频表获取
            }
            
            # 获取今日视频数量
            cursor.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE task_type IN ('video_editing', 'video_upload') 
                AND status = 'completed'
                AND DATE(created_time) = ?
            ''', (today,))
            
            stats['today_videos'] = cursor.fetchone()[0] or 0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {
                'today_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'running_tasks': 0,
                'today_videos': 0
            }
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务"""
        try:
            if task_id not in self.tasks:
                return {'error': '任务不存在', 'status': 'failed'}
            
            task = self.tasks[task_id]
            
            # 更新任务属性
            if 'name' in task_data:
                task.name = task_data['name']
            if 'priority' in task_data:
                task.priority = TaskPriority(task_data['priority'])
            if 'params' in task_data:
                task.params.update(task_data['params'])
            if 'status' in task_data:
                task.status = TaskStatus(task_data['status'])
            if 'progress' in task_data:
                task.progress = task_data['progress']
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            logger.info(f"任务更新成功: {task.name} ({task_id})")
            
            return {
                'id': task_id,
                'status': 'updated',
                'message': '任务更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """删除任务"""
        try:
            # 如果任务正在运行，先取消
            if task_id in self.running_tasks:
                self.cancel_task(task_id)
            
            # 从内存缓存删除
            if task_id in self.tasks:
                del self.tasks[task_id]
            
            # 从数据库删除
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            cursor.execute('DELETE FROM task_logs WHERE task_id = ?', (task_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"任务删除成功: {task_id}")
            
            return {
                'id': task_id,
                'status': 'deleted',
                'message': '任务删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.completed_time = datetime.now()
                
                # 如果任务正在运行，尝试停止
                if task_id in self.running_tasks:
                    future = self.running_tasks[task_id]
                    future.cancel()
                    del self.running_tasks[task_id]
                
                # 保存到数据库
                self._save_task_to_db(task)
                
                logger.info(f"任务取消成功: {task.name} ({task_id})")
                
                return {
                    'id': task_id,
                    'status': 'cancelled',
                    'message': '任务取消成功'
                }
            
            return {'error': '任务不存在', 'status': 'failed'}
            
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def start_scheduler(self):
        """启动任务调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务调度器已启动")
    
    def stop_scheduler(self):
        """停止任务调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # 停止所有运行中的任务
        for task_id, future in self.running_tasks.items():
            future.cancel()
        
        self.executor.shutdown(wait=True)
        logger.info("任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                # 检查计划任务
                self._check_scheduled_tasks()
                
                # 处理任务队列
                if not self.task_queue.empty() and len(self.running_tasks) < scheduler_config.MAX_CONCURRENT_TASKS:
                    try:
                        priority, task_id = self.task_queue.get_nowait()
                        if task_id in self.tasks:
                            self._execute_task(task_id)
                    except queue.Empty:
                        pass
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"任务调度器错误: {e}")
                time.sleep(5)
    
    def _check_scheduled_tasks(self):
        """检查计划任务"""
        try:
            now = datetime.now()
            
            for task_id, task in self.tasks.items():
                if (task.scheduled_time and 
                    task.scheduled_time <= now and 
                    task.status == TaskStatus.PENDING):
                    
                    # 添加到任务队列
                    self.task_queue.put((task.priority.value * -1, task_id))
                    logger.info(f"计划任务已加入队列: {task.name} ({task_id})")
                    
        except Exception as e:
            logger.error(f"检查计划任务失败: {e}")
    
    def _execute_task(self, task_id: str):
        """执行任务"""
        try:
            task = self.tasks[task_id]
            
            # 检查任务处理器
            if task.task_type not in self.task_handlers:
                task.status = TaskStatus.FAILED
                task.error_message = f"未找到任务处理器: {task.task_type}"
                self._save_task_to_db(task)
                return
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_time = datetime.now()
            self._save_task_to_db(task)
            
            # 提交任务到线程池
            handler = self.task_handlers[task.task_type]
            future = self.executor.submit(self._run_task_with_timeout, task, handler)
            self.running_tasks[task_id] = future
            
            # 添加完成回调
            future.add_done_callback(lambda f: self._task_completed(task_id, f))
            
            logger.info(f"任务开始执行: {task.name} ({task_id})")
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_time = datetime.now()
                self._save_task_to_db(task)
    
    def _run_task_with_timeout(self, task: Task, handler: Callable):
        """带超时的任务执行"""
        try:
            # 执行任务处理器
            result = handler(task)
            return result
            
        except Exception as e:
            logger.error(f"任务执行异常: {task.name} - {e}")
            raise
    
    def _task_completed(self, task_id: str, future):
        """任务完成回调"""
        try:
            # 从运行任务列表移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.completed_time = datetime.now()
            
            try:
                # 获取任务结果
                result = future.result()
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = 100
                
                logger.info(f"任务完成: {task.name} ({task_id})")
                
            except Exception as e:
                # 任务执行失败
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                
                # 检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.RETRYING
                    
                    # 重新加入队列
                    self.task_queue.put((task.priority.value * -1, task_id))
                    
                    logger.warning(f"任务失败，准备重试 ({task.retry_count}/{task.max_retries}): {task.name}")
                else:
                    logger.error(f"任务失败: {task.name} ({task_id}) - {e}")
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 更新统计
            self._update_task_stats()
            
        except Exception as e:
            logger.error(f"任务完成回调失败: {e}")
    
    def _update_task_stats(self):
        """更新任务统计"""
        try:
            today = datetime.now().date()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 计算今日统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    AVG(CASE WHEN completed_time IS NOT NULL AND started_time IS NOT NULL 
                        THEN (julianday(completed_time) - julianday(started_time)) * 86400 
                        ELSE NULL END) as avg_duration
                FROM tasks 
                WHERE DATE(created_time) = ?
            ''', (today,))
            
            row = cursor.fetchone()
            
            # 插入或更新统计
            cursor.execute('''
                INSERT OR REPLACE INTO task_stats 
                (date, total_tasks, completed_tasks, failed_tasks, avg_duration, updated_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, row[0], row[1], row[2], row[3] or 0, datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新任务统计失败: {e}")
    
    def _row_to_task_dict(self, row) -> Dict[str, Any]:
        """数据库行转换为任务字典"""
        return {
            'id': row[0],
            'name': row[1],
            'task_type': row[2],
            'priority': row[3],
            'params': json.loads(row[4]) if row[4] else {},
            'status': row[5],
            'status_text': self._get_status_text(row[5]),
            'progress': row[6],
            'result': json.loads(row[7]) if row[7] else None,
            'error_message': row[8],
            'created_time': row[9],
            'started_time': row[10],
            'completed_time': row[11],
            'scheduled_time': row[12],
            'retry_count': row[13],
            'max_retries': row[14]
        }
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'pending': '等待中',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消',
            'paused': '已暂停',
            'retrying': '重试中'
        }
        return status_map.get(status, '未知')
    
    # 默认任务处理器
    def _handle_content_fetch(self, task: Task) -> Dict[str, Any]:
        """处理内容采集任务"""
        try:
            logger.info(f"开始内容采集: {task.name}")
            
            # 导入内容存储管理器和采集模块
            from content_storage import content_storage
            from pathlib import Path
            import sys
            
            # 添加采集模块路径
            fetch_dir = Path(__file__).parent / "01_content_fetch"
            sys.path.append(str(fetch_dir))
            
            try:
                from fetch_news import NewsFetcher
                from real_api_fetcher import RealAPIFetcher
            except ImportError:
                logger.warning("采集模块导入失败，使用模拟数据")
                return self._handle_content_fetch_mock(task)
            
            # 获取任务参数
            params = task.params or {}
            source = params.get('source', 'netease')
            category = params.get('category', '热点')
            limit = params.get('limit', 10)
            
            collected_articles = []
            
            # 根据来源选择采集器
            if source == 'netease':
                task.progress = 20
                self._save_task_to_db(task)
                
                fetcher = NewsFetcher()
                articles = fetcher.fetch_netease_news(category=category, limit=limit)
                collected_articles.extend(articles)
                
            elif source == 'sina':
                task.progress = 20
                self._save_task_to_db(task)
                
                fetcher = NewsFetcher()
                articles = fetcher.fetch_sina_news(category=category, limit=limit)
                collected_articles.extend(articles)
                
            elif source == 'newsapi':
                task.progress = 20
                self._save_task_to_db(task)
                
                fetcher = RealAPIFetcher()
                articles = fetcher.fetch_newsapi(category=category, limit=limit)
                collected_articles.extend(articles)
                
            elif source == 'github':
                task.progress = 20
                self._save_task_to_db(task)
                
                fetcher = RealAPIFetcher()
                articles = fetcher.fetch_github_trending(limit=limit)
                collected_articles.extend(articles)
                
            elif source == 'hackernews':
                task.progress = 20
                self._save_task_to_db(task)
                
                fetcher = RealAPIFetcher()
                articles = fetcher.fetch_hackernews(limit=limit)
                collected_articles.extend(articles)
                
            elif source == 'all':
                # 从多个来源采集
                fetcher = NewsFetcher()
                real_fetcher = RealAPIFetcher()
                
                task.progress = 10
                self._save_task_to_db(task)
                
                # 网易新闻
                articles = fetcher.fetch_netease_news(category=category, limit=3)
                collected_articles.extend(articles)
                
                task.progress = 30
                self._save_task_to_db(task)
                
                # GitHub Trending
                articles = real_fetcher.fetch_github_trending(limit=3)
                collected_articles.extend(articles)
                
                task.progress = 50
                self._save_task_to_db(task)
                
                # Hacker News
                articles = real_fetcher.fetch_hackernews(limit=4)
                collected_articles.extend(articles)
                
            else:
                # 默认使用网易新闻
                fetcher = NewsFetcher()
                articles = fetcher.fetch_netease_news(category=category, limit=limit)
                collected_articles.extend(articles)
            
            task.progress = 70
            self._save_task_to_db(task)
            
            # 处理采集到的文章数据
            processed_articles = []
            for article in collected_articles:
                processed_article = {
                    'title': article.get('title', ''),
                    'content': article.get('content', ''),
                    'summary': article.get('content', '')[:200] + '...' if len(article.get('content', '')) > 200 else article.get('content', ''),
                    'source': article.get('source', ''),
                    'source_url': article.get('url', ''),
                    'author': article.get('author', ''),
                    'publish_time': article.get('timestamp', ''),
                    'category': article.get('category', '未分类'),
                    'tags': article.get('keywords', []) if isinstance(article.get('keywords'), list) else [],
                    'image_url': article.get('image_url', '')
                }
                processed_articles.append(processed_article)
            
            task.progress = 80
            self._save_task_to_db(task)
            
            # 保存到内容存储
            if processed_articles:
                save_result = content_storage.save_articles(task.id, processed_articles)
                logger.info(f"内容保存结果: {save_result}")
            
            task.progress = 100
            self._save_task_to_db(task)
            
            logger.info(f"内容采集完成: 采集到 {len(processed_articles)} 篇文章")
            
            return {
                'message': '内容采集完成',
                'articles_count': len(processed_articles),
                'source': source,
                'category': category,
                'saved_articles': len(processed_articles)
            }
            
        except Exception as e:
            logger.error(f"内容采集失败: {e}")
            # 如果真实采集失败，使用模拟数据
            return self._handle_content_fetch_mock(task)
    
    def _handle_content_fetch_mock(self, task: Task) -> Dict[str, Any]:
        """模拟内容采集任务"""
        try:
            logger.info(f"使用模拟数据进行内容采集: {task.name}")
            
            from content_storage import content_storage
            from datetime import datetime
            import time
            
            # 模拟采集过程
            for i in range(5):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 20
                self._save_task_to_db(task)
            
            # 创建模拟文章数据
            mock_articles = [
                {
                    'title': 'AI技术发展迅速，ChatGPT引领新时代',
                    'content': '人工智能技术正在快速发展，ChatGPT等大语言模型的出现标志着AI技术进入了新的发展阶段。这些技术不仅在文本生成方面表现出色，还在代码编写、创意写作等多个领域展现出强大的能力。',
                    'summary': '人工智能技术正在快速发展，ChatGPT等大语言模型的出现标志着AI技术进入了新的发展阶段...',
                    'source': '科技日报',
                    'source_url': 'https://example.com/ai-news-1',
                    'author': '张三',
                    'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'category': '科技',
                    'tags': ['AI', '人工智能', 'ChatGPT', '技术'],
                    'image_url': ''
                },
                {
                    'title': '新能源汽车市场持续增长',
                    'content': '随着环保意识的提升和政策支持，新能源汽车市场呈现出强劲的增长势头。各大汽车厂商纷纷加大在新能源领域的投入，推出更多高性能、长续航的电动汽车产品。',
                    'summary': '随着环保意识的提升和政策支持，新能源汽车市场呈现出强劲的增长势头...',
                    'source': '汽车之家',
                    'source_url': 'https://example.com/ev-news-1',
                    'author': '李四',
                    'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'category': '汽车',
                    'tags': ['新能源', '电动汽车', '环保', '市场'],
                    'image_url': ''
                },
                {
                    'title': '5G技术推动智慧城市建设',
                    'content': '5G技术的广泛应用正在推动智慧城市建设进入新阶段。从智能交通到智慧医疗，从智能安防到智慧教育，5G技术为城市管理和服务提供了强有力的技术支撑。',
                    'summary': '5G技术的广泛应用正在推动智慧城市建设进入新阶段...',
                    'source': '通信世界',
                    'source_url': 'https://example.com/5g-news-1',
                    'author': '王五',
                    'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'category': '科技',
                    'tags': ['5G', '智慧城市', '通信', '技术'],
                    'image_url': ''
                },
                {
                    'title': '区块链技术在金融领域的应用',
                    'content': '区块链技术凭借其去中心化、不可篡改的特性，在金融领域得到了广泛应用。从数字货币到智能合约，从供应链金融到跨境支付，区块链正在重塑金融行业的未来。',
                    'summary': '区块链技术凭借其去中心化、不可篡改的特性，在金融领域得到了广泛应用...',
                    'source': '金融时报',
                    'source_url': 'https://example.com/blockchain-news-1',
                    'author': '赵六',
                    'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'category': '金融',
                    'tags': ['区块链', '金融', '数字货币', '技术'],
                    'image_url': ''
                },
                {
                    'title': '元宇宙概念持续升温',
                    'content': '元宇宙作为虚拟世界与现实世界融合的新概念，正在吸引越来越多的关注。各大科技公司纷纷布局元宇宙相关技术和应用，预计未来几年将迎来快速发展期。',
                    'summary': '元宇宙作为虚拟世界与现实世界融合的新概念，正在吸引越来越多的关注...',
                    'source': '科技前沿',
                    'source_url': 'https://example.com/metaverse-news-1',
                    'author': '孙七',
                    'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'category': '科技',
                    'tags': ['元宇宙', 'VR', 'AR', '虚拟现实'],
                    'image_url': ''
                }
            ]
            
            # 根据任务参数调整文章数量
            params = task.params or {}
            limit = params.get('limit', 10)
            articles_to_save = mock_articles[:min(limit, len(mock_articles))]
            
            # 保存到内容存储
            save_result = content_storage.save_articles(task.id, articles_to_save)
            logger.info(f"模拟内容保存结果: {save_result}")
            
            return {
                'message': '内容采集完成',
                'articles_count': len(articles_to_save),
                'source': 'mock',
                'category': params.get('category', '热点'),
                'saved_articles': len(articles_to_save)
            }
            
        except Exception as e:
            logger.error(f"模拟内容采集失败: {e}")
            raise
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器
负责管理系统中的所有任务，包括创建、执行、监控和调度
"""

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
import uuid
import queue
import concurrent.futures

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from config import DATABASE_PATH, scheduler_config
    from config.environment import get_config
except ImportError:
    DATABASE_PATH = project_root / "data" / "tasks.db"
    
    class MockConfig:
        ENABLED = True
        MAX_CONCURRENT_TASKS = 5
        TASK_TIMEOUT = 3600
        RETRY_ATTEMPTS = 3
    
    scheduler_config = MockConfig()

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Task:
    """任务类"""
    
    def __init__(self, task_id: str, name: str, task_type: str, 
                 priority: TaskPriority = TaskPriority.NORMAL,
                 params: Dict[str, Any] = None,
                 scheduled_time: Optional[datetime] = None):
        self.id = task_id
        self.name = name
        self.task_type = task_type
        self.priority = priority
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error_message = None
        self.created_time = datetime.now()
        self.started_time = None
        self.completed_time = None
        self.scheduled_time = scheduled_time
        self.retry_count = 0
        self.max_retries = scheduler_config.RETRY_ATTEMPTS
        self.timeout = scheduler_config.TASK_TIMEOUT
        self.dependencies = []
        self.callback = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'priority': self.priority.value,
            'params': self.params,
            'status': self.status.value,
            'status_text': self.get_status_text(),
            'progress': self.progress,
            'result': self.result,
            'error_message': self.error_message,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'started_time': self.started_time.isoformat() if self.started_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'duration': self.get_duration()
        }
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        status_map = {
            TaskStatus.PENDING: '等待中',
            TaskStatus.RUNNING: '运行中',
            TaskStatus.COMPLETED: '已完成',
            TaskStatus.FAILED: '失败',
            TaskStatus.CANCELLED: '已取消',
            TaskStatus.PAUSED: '已暂停',
            TaskStatus.RETRYING: '重试中'
        }
        return status_map.get(self.status, '未知')
    
    def get_duration(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if self.started_time:
            end_time = self.completed_time or datetime.now()
            return (end_time - self.started_time).total_seconds()
        return None

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        # 确保使用当前目录的数据库路径
        self.db_path = Path(__file__).parent / "tasks.db"
        self.tasks = {}  # 内存中的任务缓存
        self.task_queue = queue.PriorityQueue()
        self.running_tasks = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=scheduler_config.MAX_CONCURRENT_TASKS
        )
        self.is_running = False
        self.scheduler_thread = None
        
        # 任务处理器注册表
        self.task_handlers = {}
        
        # 初始化数据库
        self._init_database()
        
        # 注册默认任务处理器
        self._register_default_handlers()
        
        # 启动任务调度器
        if scheduler_config.ENABLED:
            self.start_scheduler()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
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
            
            logger.info("任务管理数据库初始化完成")
            
        except Exception as e:
            logger.error(f"任务管理数据库初始化失败: {e}")
            raise
    
    def _register_default_handlers(self):
        """注册默认任务处理器"""
        self.register_handler('content_fetch', self._handle_content_fetch)
        self.register_handler('script_generation', self._handle_script_generation)
        self.register_handler('tts_generation', self._handle_tts_generation)
        self.register_handler('video_editing', self._handle_video_editing)
        self.register_handler('thumbnail_generation', self._handle_thumbnail_generation)
        self.register_handler('video_upload', self._handle_video_upload)
        self.register_handler('content_review', self._handle_content_review)
        self.register_handler('data_analysis', self._handle_data_analysis)
        self.register_handler('system_maintenance', self._handle_system_maintenance)
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"已注册任务处理器: {task_type}")
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        try:
            # 验证必需字段
            if not task_data.get('name'):
                return {
                    'error': '任务名称不能为空',
                    'status': 'failed'
                }
            
            if not task_data.get('task_type'):
                return {
                    'error': '任务类型不能为空',
                    'status': 'failed'
                }
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 解析优先级
            priority_value = int(task_data.get('priority', 2))
            if priority_value not in [1, 2, 3, 4]:
                priority_value = 2
            priority = TaskPriority(priority_value)
            
            # 解析计划时间
            scheduled_time = None
            if task_data.get('scheduled_time'):
                try:
                    scheduled_time = datetime.fromisoformat(task_data['scheduled_time'].replace('T', ' '))
                except ValueError:
                    # 如果时间格式不正确，忽略计划时间
                    pass
            
            # 创建任务对象
            task = Task(
                task_id=task_id,
                name=str(task_data['name']),
                task_type=str(task_data['task_type']),
                priority=priority,
                params=task_data.get('params', {}),
                scheduled_time=scheduled_time
            )
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 添加到内存缓存
            self.tasks[task_id] = task
            
            logger.info(f"任务已保存到数据库和内存缓存: {task_id}")
            
            # 添加到任务队列
            if not scheduled_time or scheduled_time <= datetime.now():
                self.task_queue.put((priority.value * -1, task_id))  # 负值用于优先级排序
            
            logger.info(f"任务创建成功: {task.name} ({task_id})")
            
            return {
                'id': task_id,
                'status': 'created',
                'message': '任务创建成功',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'success': False
            }
    
    def _save_task_to_db(self, task: Task):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, name, task_type, priority, params, status, progress, 
                 result, error_message, created_time, started_time, completed_time,
                 scheduled_time, retry_count, max_retries, timeout, dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.name, task.task_type, task.priority.value,
                json.dumps(task.params), task.status.value, task.progress,
                json.dumps(task.result) if task.result else None,
                task.error_message,
                task.created_time, task.started_time, task.completed_time,
                task.scheduled_time, task.retry_count, task.max_retries,
                task.timeout, json.dumps(task.dependencies)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        try:
            # 先从内存缓存获取
            if task_id in self.tasks:
                return self.tasks[task_id].to_dict()
            
            # 从数据库获取
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_task_dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def get_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的任务"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM tasks 
                ORDER BY created_time DESC 
                LIMIT ?
            ''', (limit,))
            
            tasks = []
            rows = cursor.fetchall()
            logger.info(f"从数据库获取到 {len(rows)} 个任务")
            
            for row in rows:
                task_dict = self._row_to_task_dict(row)
                tasks.append(task_dict)
                logger.debug(f"任务: {task_dict.get('name')} - {task_dict.get('id')}")
            
            conn.close()
            logger.info(f"返回任务列表，共 {len(tasks)} 个任务")
            return tasks
            
        except Exception as e:
            logger.error(f"获取最近任务失败: {e}")
            return []
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 今日任务统计
            today = datetime.now().date()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_tasks
                FROM tasks 
                WHERE DATE(created_time) = ?
            ''', (today,))
            
            row = cursor.fetchone()
            
            stats = {
                'today_tasks': row[0] or 0,
                'completed_tasks': row[1] or 0,
                'failed_tasks': row[2] or 0,
                'running_tasks': row[3] or 0,
                'today_videos': 0  # 需要从视频表获取
            }
            
            # 获取今日视频数量
            cursor.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE task_type IN ('video_editing', 'video_upload') 
                AND status = 'completed'
                AND DATE(created_time) = ?
            ''', (today,))
            
            stats['today_videos'] = cursor.fetchone()[0] or 0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {
                'today_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'running_tasks': 0,
                'today_videos': 0
            }
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务"""
        try:
            if task_id not in self.tasks:
                return {'error': '任务不存在', 'status': 'failed'}
            
            task = self.tasks[task_id]
            
            # 更新任务属性
            if 'name' in task_data:
                task.name = task_data['name']
            if 'priority' in task_data:
                task.priority = TaskPriority(task_data['priority'])
            if 'params' in task_data:
                task.params.update(task_data['params'])
            if 'status' in task_data:
                task.status = TaskStatus(task_data['status'])
            if 'progress' in task_data:
                task.progress = task_data['progress']
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            logger.info(f"任务更新成功: {task.name} ({task_id})")
            
            return {
                'id': task_id,
                'status': 'updated',
                'message': '任务更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """删除任务"""
        try:
            # 如果任务正在运行，先取消
            if task_id in self.running_tasks:
                self.cancel_task(task_id)
            
            # 从内存缓存删除
            if task_id in self.tasks:
                del self.tasks[task_id]
            
            # 从数据库删除
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            cursor.execute('DELETE FROM task_logs WHERE task_id = ?', (task_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"任务删除成功: {task_id}")
            
            return {
                'id': task_id,
                'status': 'deleted',
                'message': '任务删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.completed_time = datetime.now()
                
                # 如果任务正在运行，尝试停止
                if task_id in self.running_tasks:
                    future = self.running_tasks[task_id]
                    future.cancel()
                    del self.running_tasks[task_id]
                
                # 保存到数据库
                self._save_task_to_db(task)
                
                logger.info(f"任务取消成功: {task.name} ({task_id})")
                
                return {
                    'id': task_id,
                    'status': 'cancelled',
                    'message': '任务取消成功'
                }
            
            return {'error': '任务不存在', 'status': 'failed'}
            
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def start_scheduler(self):
        """启动任务调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务调度器已启动")
    
    def stop_scheduler(self):
        """停止任务调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # 停止所有运行中的任务
        for task_id, future in self.running_tasks.items():
            future.cancel()
        
        self.executor.shutdown(wait=True)
        logger.info("任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                # 检查计划任务
                self._check_scheduled_tasks()
                
                # 处理任务队列
                if not self.task_queue.empty() and len(self.running_tasks) < scheduler_config.MAX_CONCURRENT_TASKS:
                    try:
                        priority, task_id = self.task_queue.get_nowait()
                        if task_id in self.tasks:
                            self._execute_task(task_id)
                    except queue.Empty:
                        pass
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"任务调度器错误: {e}")
                time.sleep(5)
    
    def _check_scheduled_tasks(self):
        """检查计划任务"""
        try:
            now = datetime.now()
            
            for task_id, task in self.tasks.items():
                if (task.scheduled_time and 
                    task.scheduled_time <= now and 
                    task.status == TaskStatus.PENDING):
                    
                    # 添加到任务队列
                    self.task_queue.put((task.priority.value * -1, task_id))
                    logger.info(f"计划任务已加入队列: {task.name} ({task_id})")
                    
        except Exception as e:
            logger.error(f"检查计划任务失败: {e}")
    
    def _execute_task(self, task_id: str):
        """执行任务"""
        try:
            task = self.tasks[task_id]
            
            # 检查任务处理器
            if task.task_type not in self.task_handlers:
                task.status = TaskStatus.FAILED
                task.error_message = f"未找到任务处理器: {task.task_type}"
                self._save_task_to_db(task)
                return
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_time = datetime.now()
            self._save_task_to_db(task)
            
            # 提交任务到线程池
            handler = self.task_handlers[task.task_type]
            future = self.executor.submit(self._run_task_with_timeout, task, handler)
            self.running_tasks[task_id] = future
            
            # 添加完成回调
            future.add_done_callback(lambda f: self._task_completed(task_id, f))
            
            logger.info(f"任务开始执行: {task.name} ({task_id})")
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_time = datetime.now()
                self._save_task_to_db(task)
    
    def _run_task_with_timeout(self, task: Task, handler: Callable):
        """带超时的任务执行"""
        try:
            # 执行任务处理器
            result = handler(task)
            return result
            
        except Exception as e:
            logger.error(f"任务执行异常: {task.name} - {e}")
            raise
    
    def _task_completed(self, task_id: str, future):
        """任务完成回调"""
        try:
            # 从运行任务列表移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.completed_time = datetime.now()
            
            try:
                # 获取任务结果
                result = future.result()
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = 100
                
                logger.info(f"任务完成: {task.name} ({task_id})")
                
            except Exception as e:
                # 任务执行失败
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                
                # 检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.RETRYING
                    
                    # 重新加入队列
                    self.task_queue.put((task.priority.value * -1, task_id))
                    
                    logger.warning(f"任务失败，准备重试 ({task.retry_count}/{task.max_retries}): {task.name}")
                else:
                    logger.error(f"任务失败: {task.name} ({task_id}) - {e}")
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 更新统计
            self._update_task_stats()
            
        except Exception as e:
            logger.error(f"任务完成回调失败: {e}")
    
    def _update_task_stats(self):
        """更新任务统计"""
        try:
            today = datetime.now().date()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 计算今日统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    AVG(CASE WHEN completed_time IS NOT NULL AND started_time IS NOT NULL 
                        THEN (julianday(completed_time) - julianday(started_time)) * 86400 
                        ELSE NULL END) as avg_duration
                FROM tasks 
                WHERE DATE(created_time) = ?
            ''', (today,))
            
            row = cursor.fetchone()
            
            # 插入或更新统计
            cursor.execute('''
                INSERT OR REPLACE INTO task_stats 
                (date, total_tasks, completed_tasks, failed_tasks, avg_duration, updated_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, row[0], row[1], row[2], row[3] or 0, datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新任务统计失败: {e}")
    
    def _row_to_task_dict(self, row) -> Dict[str, Any]:
        """数据库行转换为任务字典"""
        return {
            'id': row[0],
            'name': row[1],
            'task_type': row[2],
            'priority': row[3],
            'params': json.loads(row[4]) if row[4] else {},
            'status': row[5],
            'status_text': self._get_status_text(row[5]),
            'progress': row[6],
            'result': json.loads(row[7]) if row[7] else None,
            'error_message': row[8],
            'created_time': row[9],
            'started_time': row[10],
            'completed_time': row[11],
            'scheduled_time': row[12],
            'retry_count': row[13],
            'max_retries': row[14]
        }
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'pending': '等待中',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消',
            'paused': '已暂停',
            'retrying': '重试中'
        }
        return status_map.get(status, '未知')
    
    # 默认任务处理器
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器
负责管理系统中的所有任务，包括创建、执行、监控和调度
"""

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
import uuid
import queue
import concurrent.futures

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from config import DATABASE_PATH, scheduler_config
    from config.environment import get_config
except ImportError:
    DATABASE_PATH = project_root / "data" / "tasks.db"
    
    class MockConfig:
        ENABLED = True
        MAX_CONCURRENT_TASKS = 5
        TASK_TIMEOUT = 3600
        RETRY_ATTEMPTS = 3
    
    scheduler_config = MockConfig()

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Task:
    """任务类"""
    
    def __init__(self, task_id: str, name: str, task_type: str, 
                 priority: TaskPriority = TaskPriority.NORMAL,
                 params: Dict[str, Any] = None,
                 scheduled_time: Optional[datetime] = None):
        self.id = task_id
        self.name = name
        self.task_type = task_type
        self.priority = priority
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error_message = None
        self.created_time = datetime.now()
        self.started_time = None
        self.completed_time = None
        self.scheduled_time = scheduled_time
        self.retry_count = 0
        self.max_retries = scheduler_config.RETRY_ATTEMPTS
        self.timeout = scheduler_config.TASK_TIMEOUT
        self.dependencies = []
        self.callback = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'priority': self.priority.value,
            'params': self.params,
            'status': self.status.value,
            'status_text': self.get_status_text(),
            'progress': self.progress,
            'result': self.result,
            'error_message': self.error_message,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'started_time': self.started_time.isoformat() if self.started_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'duration': self.get_duration()
        }
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        status_map = {
            TaskStatus.PENDING: '等待中',
            TaskStatus.RUNNING: '运行中',
            TaskStatus.COMPLETED: '已完成',
            TaskStatus.FAILED: '失败',
            TaskStatus.CANCELLED: '已取消',
            TaskStatus.PAUSED: '已暂停',
            TaskStatus.RETRYING: '重试中'
        }
        return status_map.get(self.status, '未知')
    
    def get_duration(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if self.started_time:
            end_time = self.completed_time or datetime.now()
            return (end_time - self.started_time).total_seconds()
        return None

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        # 确保使用当前目录的数据库路径
        self.db_path = Path(__file__).parent / "tasks.db"
        self.tasks = {}  # 内存中的任务缓存
        self.task_queue = queue.PriorityQueue()
        self.running_tasks = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=scheduler_config.MAX_CONCURRENT_TASKS
        )
        self.is_running = False
        self.scheduler_thread = None
        
        # 任务处理器注册表
        self.task_handlers = {}
        
        # 初始化数据库
        self._init_database()
        
        # 注册默认任务处理器
        self._register_default_handlers()
        
        # 启动任务调度器
        if scheduler_config.ENABLED:
            self.start_scheduler()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
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
            
            logger.info("任务管理数据库初始化完成")
            
        except Exception as e:
            logger.error(f"任务管理数据库初始化失败: {e}")
            raise
    
    def _register_default_handlers(self):
        """注册默认任务处理器"""
        self.register_handler('content_fetch', self._handle_content_fetch)
        self.register_handler('script_generation', self._handle_script_generation)
        self.register_handler('tts_generation', self._handle_tts_generation)
        self.register_handler('video_editing', self._handle_video_editing)
        self.register_handler('thumbnail_generation', self._handle_thumbnail_generation)
        self.register_handler('video_upload', self._handle_video_upload)
        self.register_handler('content_review', self._handle_content_review)
        self.register_handler('data_analysis', self._handle_data_analysis)
        self.register_handler('system_maintenance', self._handle_system_maintenance)
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"已注册任务处理器: {task_type}")
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        try:
            # 验证必需字段
            if not task_data.get('name'):
                return {
                    'error': '任务名称不能为空',
                    'status': 'failed'
                }
            
            if not task_data.get('task_type'):
                return {
                    'error': '任务类型不能为空',
                    'status': 'failed'
                }
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 解析优先级
            priority_value = int(task_data.get('priority', 2))
            if priority_value not in [1, 2, 3, 4]:
                priority_value = 2
            priority = TaskPriority(priority_value)
            
            # 解析计划时间
            scheduled_time = None
            if task_data.get('scheduled_time'):
                try:
                    scheduled_time = datetime.fromisoformat(task_data['scheduled_time'].replace('T', ' '))
                except ValueError:
                    # 如果时间格式不正确，忽略计划时间
                    pass
            
            # 创建任务对象
            task = Task(
                task_id=task_id,
                name=str(task_data['name']),
                task_type=str(task_data['task_type']),
                priority=priority,
                params=task_data.get('params', {}),
                scheduled_time=scheduled_time
            )
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 添加到内存缓存
            self.tasks[task_id] = task
            
            logger.info(f"任务已保存到数据库和内存缓存: {task_id}")
            
            # 添加到任务队列
            if not scheduled_time or scheduled_time <= datetime.now():
                self.task_queue.put((priority.value * -1, task_id))  # 负值用于优先级排序
            
            logger.info(f"任务创建成功: {task.name} ({task_id})")
            
            return {
                'id': task_id,
                'status': 'created',
                'message': '任务创建成功',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'success': False
            }
    
    def _save_task_to_db(self, task: Task):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, name, task_type, priority, params, status, progress, 
                 result, error_message, created_time, started_time, completed_time,
                 scheduled_time, retry_count, max_retries, timeout, dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.name, task.task_type, task.priority.value,
                json.dumps(task.params), task.status.value, task.progress,
                json.dumps(task.result) if task.result else None,
                task.error_message,
                task.created_time, task.started_time, task.completed_time,
                task.scheduled_time, task.retry_count, task.max_retries,
                task.timeout, json.dumps(task.dependencies)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        try:
            # 先从内存缓存获取
            if task_id in self.tasks:
                return self.tasks[task_id].to_dict()
            
            # 从数据库获取
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_task_dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def get_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的任务"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM tasks 
                ORDER BY created_time DESC 
                LIMIT ?
            ''', (limit,))
            
            tasks = []
            rows = cursor.fetchall()
            logger.info(f"从数据库获取到 {len(rows)} 个任务")
            
            for row in rows:
                task_dict = self._row_to_task_dict(row)
                tasks.append(task_dict)
                logger.debug(f"任务: {task_dict.get('name')} - {task_dict.get('id')}")
            
            conn.close()
            logger.info(f"返回任务列表，共 {len(tasks)} 个任务")
            return tasks
            
        except Exception as e:
            logger.error(f"获取最近任务失败: {e}")
            return []
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 今日任务统计
            today = datetime.now().date()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_tasks
                FROM tasks 
                WHERE DATE(created_time) = ?
            ''', (today,))
            
            row = cursor.fetchone()
            
            stats = {
                'today_tasks': row[0] or 0,
                'completed_tasks': row[1] or 0,
                'failed_tasks': row[2] or 0,
                'running_tasks': row[3] or 0,
                'today_videos': 0  # 需要从视频表获取
            }
            
            # 获取今日视频数量
            cursor.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE task_type IN ('video_editing', 'video_upload') 
                AND status = 'completed'
                AND DATE(created_time) = ?
            ''', (today,))
            
            stats['today_videos'] = cursor.fetchone()[0] or 0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {
                'today_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'running_tasks': 0,
                'today_videos': 0
            }
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务"""
        try:
            if task_id not in self.tasks:
                return {'error': '任务不存在', 'status': 'failed'}
            
            task = self.tasks[task_id]
            
            # 更新任务属性
            if 'name' in task_data:
                task.name = task_data['name']
            if 'priority' in task_data:
                task.priority = TaskPriority(task_data['priority'])
            if 'params' in task_data:
                task.params.update(task_data['params'])
            if 'status' in task_data:
                task.status = TaskStatus(task_data['status'])
            if 'progress' in task_data:
                task.progress = task_data['progress']
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            logger.info(f"任务更新成功: {task.name} ({task_id})")
            
            return {
                'id': task_id,
                'status': 'updated',
                'message': '任务更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """删除任务"""
        try:
            # 如果任务正在运行，先取消
            if task_id in self.running_tasks:
                self.cancel_task(task_id)
            
            # 从内存缓存删除
            if task_id in self.tasks:
                del self.tasks[task_id]
            
            # 从数据库删除
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            cursor.execute('DELETE FROM task_logs WHERE task_id = ?', (task_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"任务删除成功: {task_id}")
            
            return {
                'id': task_id,
                'status': 'deleted',
                'message': '任务删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.completed_time = datetime.now()
                
                # 如果任务正在运行，尝试停止
                if task_id in self.running_tasks:
                    future = self.running_tasks[task_id]
                    future.cancel()
                    del self.running_tasks[task_id]
                
                # 保存到数据库
                self._save_task_to_db(task)
                
                logger.info(f"任务取消成功: {task.name} ({task_id})")
                
                return {
                    'id': task_id,
                    'status': 'cancelled',
                    'message': '任务取消成功'
                }
            
            return {'error': '任务不存在', 'status': 'failed'}
            
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def start_scheduler(self):
        """启动任务调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务调度器已启动")
    
    def stop_scheduler(self):
        """停止任务调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # 停止所有运行中的任务
        for task_id, future in self.running_tasks.items():
            future.cancel()
        
        self.executor.shutdown(wait=True)
        logger.info("任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                # 检查计划任务
                self._check_scheduled_tasks()
                
                # 处理任务队列
                if not self.task_queue.empty() and len(self.running_tasks) < scheduler_config.MAX_CONCURRENT_TASKS:
                    try:
                        priority, task_id = self.task_queue.get_nowait()
                        if task_id in self.tasks:
                            self._execute_task(task_id)
                    except queue.Empty:
                        pass
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"任务调度器错误: {e}")
                time.sleep(5)
    
    def _check_scheduled_tasks(self):
        """检查计划任务"""
        try:
            now = datetime.now()
            
            for task_id, task in self.tasks.items():
                if (task.scheduled_time and 
                    task.scheduled_time <= now and 
                    task.status == TaskStatus.PENDING):
                    
                    # 添加到任务队列
                    self.task_queue.put((task.priority.value * -1, task_id))
                    logger.info(f"计划任务已加入队列: {task.name} ({task_id})")
                    
        except Exception as e:
            logger.error(f"检查计划任务失败: {e}")
    
    def _execute_task(self, task_id: str):
        """执行任务"""
        try:
            task = self.tasks[task_id]
            
            # 检查任务处理器
            if task.task_type not in self.task_handlers:
                task.status = TaskStatus.FAILED
                task.error_message = f"未找到任务处理器: {task.task_type}"
                self._save_task_to_db(task)
                return
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_time = datetime.now()
            self._save_task_to_db(task)
            
            # 提交任务到线程池
            handler = self.task_handlers[task.task_type]
            future = self.executor.submit(self._run_task_with_timeout, task, handler)
            self.running_tasks[task_id] = future
            
            # 添加完成回调
            future.add_done_callback(lambda f: self._task_completed(task_id, f))
            
            logger.info(f"任务开始执行: {task.name} ({task_id})")
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_time = datetime.now()
                self._save_task_to_db(task)
    
    def _run_task_with_timeout(self, task: Task, handler: Callable):
        """带超时的任务执行"""
        try:
            # 执行任务处理器
            result = handler(task)
            return result
            
        except Exception as e:
            logger.error(f"任务执行异常: {task.name} - {e}")
            raise
    
    def _task_completed(self, task_id: str, future):
        """任务完成回调"""
        try:
            # 从运行任务列表移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.completed_time = datetime.now()
            
            try:
                # 获取任务结果
                result = future.result()
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = 100
                
                logger.info(f"任务完成: {task.name} ({task_id})")
                
            except Exception as e:
                # 任务执行失败
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                
                # 检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.RETRYING
                    
                    # 重新加入队列
                    self.task_queue.put((task.priority.value * -1, task_id))
                    
                    logger.warning(f"任务失败，准备重试 ({task.retry_count}/{task.max_retries}): {task.name}")
                else:
                    logger.error(f"任务失败: {task.name} ({task_id}) - {e}")
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 更新统计
            self._update_task_stats()
            
        except Exception as e:
            logger.error(f"任务完成回调失败: {e}")
    
    def _update_task_stats(self):
        """更新任务统计"""
        try:
            today = datetime.now().date()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 计算今日统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    AVG(CASE WHEN completed_time IS NOT NULL AND started_time IS NOT NULL 
                        THEN (julianday(completed_time) - julianday(started_time)) * 86400 
                        ELSE NULL END) as avg_duration
                FROM tasks 
                WHERE DATE(created_time) = ?
            ''', (today,))
            
            row = cursor.fetchone()
            
            # 插入或更新统计
            cursor.execute('''
                INSERT OR REPLACE INTO task_stats 
                (date, total_tasks, completed_tasks, failed_tasks, avg_duration, updated_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, row[0], row[1], row[2], row[3] or 0, datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新任务统计失败: {e}")
    
    def _row_to_task_dict(self, row) -> Dict[str, Any]:
        """数据库行转换为任务字典"""
        return {
            'id': row[0],
            'name': row[1],
            'task_type': row[2],
            'priority': row[3],
            'params': json.loads(row[4]) if row[4] else {},
            'status': row[5],
            'status_text': self._get_status_text(row[5]),
            'progress': row[6],
            'result': json.loads(row[7]) if row[7] else None,
            'error_message': row[8],
            'created_time': row[9],
            'started_time': row[10],
            'completed_time': row[11],
            'scheduled_time': row[12],
            'retry_count': row[13],
            'max_retries': row[14]
        }
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'pending': '等待中',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消',
            'paused': '已暂停',
            'retrying': '重试中'
        }
        return status_map.get(status, '未知')
    
    # 默认任务处理器
    def _handle_content_fetch(self, task: Task) -> Dict[str, Any]:
        """处理内容采集任务"""
        try:
            logger.info(f"开始内容采集: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(10):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 10
                self._save_task_to_db(task)
            
            return {'message': '内容采集完成', 'articles_count': 10}
            
        except Exception as e:
            logger.error(f"内容采集失败: {e}")
            raise
    
    def _handle_script_generation(self, task: Task) -> Dict[str, Any]:
        """处理脚本生成任务"""
        try:
            logger.info(f"开始脚本生成: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(5):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(2)
                task.progress = (i + 1) * 20
                self._save_task_to_db(task)
            
            return {'message': '脚本生成完成', 'script_length': 500}
            
        except Exception as e:
            logger.error(f"脚本生成失败: {e}")
            raise
    
    def _handle_tts_generation(self, task: Task) -> Dict[str, Any]:
        """处理TTS生成任务"""
        try:
            logger.info(f"开始TTS生成: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(8):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 12.5
                self._save_task_to_db(task)
            
            return {'message': 'TTS生成完成', 'audio_duration': 120}
            
        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            raise
    
    def _handle_video_editing(self, task: Task) -> Dict[str, Any]:
        """处理视频剪辑任务"""
        try:
            logger.info(f"开始视频剪辑: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(15):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(2)
                task.progress = (i + 1) * 6.67
                self._save_task_to_db(task)
            
            return {'message': '视频剪辑完成', 'output_file': 'video_output.mp4'}
            
        except Exception as e:
            logger.error(f"视频剪辑失败: {e}")
            raise
    
    def _handle_thumbnail_generation(self, task: Task) -> Dict[str, Any]:
        """处理封面生成任务"""
        try:
            logger.info(f"开始封面生成: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(3):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 33.33
                self._save_task_to_db(task)
            
            return {'message': '封面生成完成', 'thumbnail_file': 'thumbnail.jpg'}
            
        except Exception as e:
            logger.error(f"封面生成失败: {e}")
            raise
    
    def _handle_video_upload(self, task: Task) -> Dict[str, Any]:
        """处理视频上传任务"""
        try:
            logger.info(f"开始视频上传: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(20):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 5
                self._save_task_to_db(task)
            
            return {'message': '视频上传完成', 'upload_urls': ['platform1', 'platform2']}
            
        except Exception as e:
            logger.error(f"视频上传失败: {e}")
            raise
    
    def _handle_content_review(self, task: Task) -> Dict[str, Any]:
        """处理内容审核任务"""
        try:
            logger.info(f"开始内容审核: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(5):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 20
                self._save_task_to_db(task)
            
            return {'message': '内容审核完成', 'review_result': 'approved'}
            
        except Exception as e:
            logger.error(f"内容审核失败: {e}")
            raise
    
    def _handle_data_analysis(self, task: Task) -> Dict[str, Any]:
        """处理数据分析任务"""
        try:
            logger.info(f"开始数据分析: {task.name}")
            
            # 模拟任务执行
            import time
            for i in range(10):
                if task.status == TaskStatus.CANCELLED:
                    break
                time.sleep(1)
                task.progress = (i + 1) * 10
                self._save_task_to_db(task)
            
            return {'message': '数据分析完成', 'analysis_report': 'report.json'}
            
        except Exception as e:
            logger.error(f"数据分析失败: {e}")
            raise
    
    def _handle_system_maintenance(self, task: Task) -> Dict[str, Any]:
        """处理系统维护任务"""
        try:
            logger.info(f"开始系统维护: {task.name}")
            
            # 模拟任务执行
            import time
            maintenance_tasks = []
            
            # 清理临时文件
            task.progress = 20
            self._save_task_to_db(task)
            time.sleep(2)
            maintenance_tasks.append("清理临时文件")
            
            # 优化数据库
            task.progress = 40
            self._save_task_to_db(task)
            time.sleep(3)
            maintenance_tasks.append("优化数据库")
            
            # 清理日志文件
            task.progress = 60
            self._save_task_to_db(task)
            time.sleep(2)
            maintenance_tasks.append("清理日志文件")
            
            # 检查系统状态
            task.progress = 80
            self._save_task_to_db(task)
            time.sleep(2)
            maintenance_tasks.append("检查系统状态")
            
            # 完成
            task.progress = 100
            self._save_task_to_db(task)
            
            return {'message': '系统维护完成', 'maintenance_tasks': maintenance_tasks}
            
        except Exception as e:
            logger.error(f"系统维护失败: {e}")
            raise
    
    def add_task_log(self, task_id: str, level: str, message: str):
        """添加任务日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO task_logs (task_id, level, message)
                VALUES (?, ?, ?)
            ''', (task_id, level, message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"添加任务日志失败: {e}")
    
    def get_task_logs(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT level, message, timestamp
                FROM task_logs
                WHERE task_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (task_id, limit))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'level': row[0],
                    'message': row[1],
                    'timestamp': row[2]
                })
            
            conn.close()
            return logs
            
        except Exception as e:
            logger.error(f"获取任务日志失败: {e}")
            return []
    
    def get_task_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取指定天数内的统计
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            cursor.execute('''
                SELECT 
                    DATE(created_time) as date,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                    AVG(CASE WHEN completed_time IS NOT NULL AND started_time IS NOT NULL 
                        THEN (julianday(completed_time) - julianday(started_time)) * 86400 
                        ELSE NULL END) as avg_duration
                FROM tasks 
                WHERE DATE(created_time) >= ?
                GROUP BY DATE(created_time)
                ORDER BY date DESC
            ''', (start_date,))
            
            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    'date': row[0],
                    'total_tasks': row[1],
                    'completed_tasks': row[2],
                    'failed_tasks': row[3],
                    'avg_duration': row[4] or 0
                })
            
            # 获取任务类型统计
            cursor.execute('''
                SELECT 
                    task_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
                FROM tasks 
                WHERE DATE(created_time) >= ?
                GROUP BY task_type
                ORDER BY count DESC
            ''', (start_date,))
            
            task_type_stats = []
            for row in cursor.fetchall():
                task_type_stats.append({
                    'task_type': row[0],
                    'count': row[1],
                    'completed_count': row[2],
                    'success_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0
                })
            
            conn.close()
            
            return {
                'daily_stats': daily_stats,
                'task_type_stats': task_type_stats,
                'total_running_tasks': len(self.running_tasks),
                'queue_size': self.task_queue.qsize()
            }
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {
                'daily_stats': [],
                'task_type_stats': [],
                'total_running_tasks': 0,
                'queue_size': 0
            }
    
    def cleanup_old_tasks(self, days: int = 30):
        """清理旧任务"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除旧任务
            cursor.execute('''
                DELETE FROM tasks 
                WHERE created_time < ? AND status IN ('completed', 'failed', 'cancelled')
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            
            # 删除相关日志
            cursor.execute('''
                DELETE FROM task_logs 
                WHERE task_id NOT IN (SELECT id FROM tasks)
            ''', )
            
            conn.commit()
            conn.close()
            
            logger.info(f"清理了 {deleted_count} 个旧任务")
            
        except Exception as e:
            logger.error(f"清理旧任务失败: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.stop_scheduler()
        except:
            pass

def main():
    """测试函数"""
    task_manager = TaskManager()
    
    print("=== 任务管理器测试 ===")
    
    # 创建测试任务
    task_data = {
        'name': '测试内容采集任务',
        'task_type': 'content_fetch',
        'priority': 2,
        'params': {'source': 'test'}
    }
    
    result = task_manager.create_task(task_data)
    print(f"创建任务结果: {result}")
    
    # 获取任务统计
    stats = task_manager.get_task_stats()
    print(f"任务统计: {stats}")
    
    # 获取最近任务
    recent_tasks = task_manager.get_recent_tasks(5)
    print(f"最近任务数量: {len(recent_tasks)}")
    
    # 等待一段时间让任务执行
    import time
    time.sleep(5)
    
    # 获取任务统计信息
    statistics = task_manager.get_task_statistics(7)
    print(f"任务统计信息: {statistics}")
    
    print("任务管理器测试完成")

if __name__ == "__main__":
    main()
