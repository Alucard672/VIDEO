#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理模块
提供任务创建、执行、监控和管理功能
"""

import logging
import threading
import time
import json
import os
import queue
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple

# 配置日志
logger = logging.getLogger(__name__)

class Task:
    """任务类"""
    
    def __init__(self, task_id: int, task_name: str, task_type: str, config: Dict[str, Any] = None):
        """初始化任务
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            task_type: 任务类型
            config: 任务配置
        """
        self.id = task_id
        self.name = task_name
        self.type = task_type
        self.config = config or {}
        self.status = "pending"  # pending, running, completed, failed, cancelled
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.completed_at = None
        self.thread = None
        self.callback = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            任务字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at
        }
    
    def update_progress(self, progress: int, result: Any = None) -> None:
        """更新任务进度
        
        Args:
            progress: 进度百分比
            result: 任务结果
        """
        self.progress = progress
        if result is not None:
            self.result = result
        self.updated_at = datetime.now().isoformat()
    
    def complete(self, result: Any = None) -> None:
        """完成任务
        
        Args:
            result: 任务结果
        """
        self.status = "completed"
        self.progress = 100
        if result is not None:
            self.result = result
        self.updated_at = datetime.now().isoformat()
        self.completed_at = self.updated_at
        
        # 调用回调函数
        if self.callback:
            self.callback(self)
    
    def fail(self, error: str) -> None:
        """任务失败
        
        Args:
            error: 错误信息
        """
        self.status = "failed"
        self.error = error
        self.updated_at = datetime.now().isoformat()
        self.completed_at = self.updated_at
        
        # 调用回调函数
        if self.callback:
            self.callback(self)
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = "cancelled"
        self.updated_at = datetime.now().isoformat()
        self.completed_at = self.updated_at
        
        # 调用回调函数
        if self.callback:
            self.callback(self)

class TaskManager:
    """任务管理器类"""
    
    def __init__(self, max_workers: int = 5):
        """初始化任务管理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.tasks = {}  # 存储所有任务
        self.task_queue = queue.Queue()  # 任务队列
        self.max_workers = max_workers
        self.workers = []  # 工作线程
        self.running = False
        self.task_handlers = {}  # 任务处理器
        self.lock = threading.Lock()
        self.next_task_id = 1
        
        # 从数据库加载任务
        self._load_tasks_from_db()
        
        logger.info(f"任务管理器初始化完成，最大工作线程数: {max_workers}")
    
    def start(self) -> None:
        """启动任务管理器"""
        if self.running:
            logger.warning("任务管理器已经在运行")
            return
        
        self.running = True
        
        # 创建工作线程
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_thread, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        # 创建任务监控线程
        monitor = threading.Thread(target=self._monitor_thread)
        monitor.daemon = True
        monitor.start()
        
        logger.info("任务管理器已启动")
    
    def stop(self) -> None:
        """停止任务管理器"""
        if not self.running:
            logger.warning("任务管理器已经停止")
            return
        
        self.running = False
        
        # 等待所有工作线程结束
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=1)
        
        logger.info("任务管理器已停止")
    
    def register_task_handler(self, task_type: str, handler: Callable[[Task], None]) -> None:
        """注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
    
    def create_task(self, task_name: str, task_type: str, config: Dict[str, Any] = None,
                   callback: Callable[[Task], None] = None) -> int:
        """创建任务
        
        Args:
            task_name: 任务名称
            task_type: 任务类型
            config: 任务配置
            callback: 任务完成回调
            
        Returns:
            任务ID
        """
        with self.lock:
            # 生成任务ID
            task_id = self._get_next_task_id()
            
            # 创建任务
            task = Task(task_id, task_name, task_type, config)
            task.callback = callback
            
            # 保存任务
            self.tasks[task_id] = task
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 加入队列
            self.task_queue.put(task_id)
            
            logger.info(f"创建任务: {task_id} - {task_name} ({task_type})")
            return task_id
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务
        
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """获取指定状态的任务
        
        Args:
            status: 任务状态
            
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_type(self, task_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的任务
        
        Args:
            task_type: 任务类型
            
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values() if task.type == task_type]
    
    def cancel_task(self, task_id: int) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        if task.status not in ["pending", "running"]:
            logger.warning(f"任务状态不允许取消: {task_id} - {task.status}")
            return False
        
        task.cancel()
        self._update_task_in_db(task)
        
        logger.info(f"取消任务: {task_id}")
        return True
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        if task.status == "running":
            logger.warning(f"任务正在运行，无法删除: {task_id}")
            return False
        
        with self.lock:
            # 从内存中删除
            if task_id in self.tasks:
                del self.tasks[task_id]
            
            # 从数据库中删除
            self._delete_task_from_db(task_id)
        
        logger.info(f"删除任务: {task_id}")
        return True
    
    def update_task_progress(self, task_id: int, progress: int, result: Any = None) -> bool:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比
            result: 任务结果
            
        Returns:
            是否更新成功
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        task.update_progress(progress, result)
        self._update_task_in_db(task)
        
        logger.debug(f"更新任务进度: {task_id} - {progress}%")
        return True
    
    def complete_task(self, task_id: int, result: Any = None) -> bool:
        """完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
            
        Returns:
            是否完成成功
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        task.complete(result)
        self._update_task_in_db(task)
        
        logger.info(f"完成任务: {task_id}")
        return True
    
    def fail_task(self, task_id: int, error: str) -> bool:
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            
        Returns:
            是否标记成功
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        task.fail(error)
        self._update_task_in_db(task)
        
        logger.info(f"任务失败: {task_id} - {error}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取任务统计
        
        Returns:
            统计信息
        """
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.status == "pending"])
        running = len([t for t in self.tasks.values() if t.status == "running"])
        completed = len([t for t in self.tasks.values() if t.status == "completed"])
        failed = len([t for t in self.tasks.values() if t.status == "failed"])
        cancelled = len([t for t in self.tasks.values() if t.status == "cancelled"])
        
        # 按类型统计
        type_stats = {}
        for task in self.tasks.values():
            if task.type not in type_stats:
                type_stats[task.type] = 0
            type_stats[task.type] += 1
        
        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "queue_size": self.task_queue.qsize(),
            "by_type": type_stats
        }
    
    def _worker_thread(self, worker_id: int) -> None:
        """工作线程
        
        Args:
            worker_id: 工作线程ID
        """
        logger.info(f"工作线程 {worker_id} 已启动")
        
        while self.running:
            try:
                # 从队列获取任务ID
                try:
                    task_id = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 获取任务
                task = self.get_task(task_id)
                if not task:
                    logger.warning(f"任务不存在: {task_id}")
                    self.task_queue.task_done()
                    continue
                
                # 检查任务状态
                if task.status != "pending":
                    logger.warning(f"任务状态不是pending: {task_id} - {task.status}")
                    self.task_queue.task_done()
                    continue
                
                # 更新任务状态
                task.status = "running"
                task.updated_at = datetime.now().isoformat()
                self._update_task_in_db(task)
                
                logger.info(f"开始执行任务: {task_id} - {task.name} ({task.type})")
                
                # 获取任务处理器
                handler = self.task_handlers.get(task.type)
                if not handler:
                    error = f"未找到任务处理器: {task.type}"
                    logger.error(error)
                    task.fail(error)
                    self._update_task_in_db(task)
                    self.task_queue.task_done()
                    continue
                
                # 执行任务
                try:
                    handler(task)
                    
                    # 如果任务没有在处理器中更新状态，则标记为完成
                    if task.status == "running":
                        task.complete()
                        self._update_task_in_db(task)
                    
                except Exception as e:
                    error = f"任务执行异常: {str(e)}"
                    logger.exception(error)
                    task.fail(error)
                    self._update_task_in_db(task)
                
                logger.info(f"任务执行完成: {task_id} - {task.status}")
                self.task_queue.task_done()
                
            except Exception as e:
                logger.exception(f"工作线程异常: {str(e)}")
    
    def _monitor_thread(self) -> None:
        """任务监控线程"""
        logger.info("任务监控线程已启动")
        
        while self.running:
            try:
                # 检查任务状态
                for task_id, task in list(self.tasks.items()):
                    # 处理超时任务
                    if task.status == "running":
                        # 这里可以添加超时检测逻辑
                        pass
                
                # 清理过期任务
                # 这里可以添加清理逻辑
                
                # 休眠
                time.sleep(60)
                
            except Exception as e:
                logger.exception(f"任务监控线程异常: {str(e)}")
                time.sleep(10)
    
    def _get_next_task_id(self) -> int:
        """获取下一个任务ID
        
        Returns:
            任务ID
        """
        task_id = self.next_task_id
        self.next_task_id += 1
        return task_id
    
    def _load_tasks_from_db(self) -> None:
        """从数据库加载任务"""
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, task_type, status, progress, 
                       created_time, created_time, completed_time, params, result, error_message
                FROM tasks
                WHERE status NOT IN ('completed', 'failed', 'cancelled')
                OR created_time > datetime('now', '-1 day')
            ''')
            
            for row in cursor.fetchall():
                task_id = row[0]
                task = Task(task_id, row[1], row[2])
                task.status = row[3]
                task.progress = row[4]
                task.created_at = row[5]
                task.updated_at = row[6]
                task.completed_at = row[7]
                
                # 解析JSON字段
                if row[8]:
                    task.config = json.loads(row[8])
                if row[9]:
                    task.result = json.loads(row[9])
                task.error = row[10]
                
                # 保存任务
                self.tasks[task_id] = task
                
                # 更新下一个任务ID
                if task_id >= self.next_task_id:
                    self.next_task_id = task_id + 1
                
                # 如果任务是pending状态，加入队列
                if task.status == "pending":
                    self.task_queue.put(task_id)
            
            conn.close()
            logger.info(f"从数据库加载了 {len(self.tasks)} 个任务")
            
        except Exception as e:
            logger.error(f"从数据库加载任务失败: {e}")
    
    def _save_task_to_db(self, task: Task) -> None:
        """保存任务到数据库
        
        Args:
            task: 任务对象
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 序列化JSON字段
            config_json = json.dumps(task.config) if task.config else None
            result_json = json.dumps(task.result) if task.result else None
            
            # 设置优先级
            priority = task.config.get('priority', 2) if task.config else 2
            
            cursor.execute('''
                INSERT INTO tasks (
                    id, name, task_name, task_type, status, progress, 
                    created_time, started_time, completed_time, params, result, error_message,
                    priority, retry_count, max_retries
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.name, task.name, task.type, task.status, task.progress,
                task.created_at, None, task.completed_at,
                config_json, result_json, task.error,
                priority, 0, 3
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}")
    
    def _update_task_in_db(self, task: Task) -> None:
        """更新数据库中的任务
        
        Args:
            task: 任务对象
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 序列化JSON字段
            config_json = json.dumps(task.config) if task.config else None
            result_json = json.dumps(task.result) if task.result else None
            
            cursor.execute('''
                UPDATE tasks SET
                    name = ?, task_name = ?, task_type = ?, status = ?, progress = ?,
                    started_time = ?, completed_time = ?, params = ?, result = ?, error_message = ?
                WHERE id = ?
            ''', (
                task.name, task.name, task.type, task.status, task.progress,
                task.updated_at, task.completed_at,
                config_json, result_json, task.error,
                task.id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新数据库中的任务失败: {e}")
    
    def _delete_task_from_db(self, task_id: int) -> None:
        """从数据库删除任务
        
        Args:
            task_id: 任务ID
        """
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"从数据库删除任务失败: {e}")

# 测试代码
if __name__ == "__main__":
    print("=== 任务管理模块测试 ===")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建任务管理器
    task_manager = TaskManager(max_workers=2)
    
    # 定义任务处理函数
    def test_task_handler(task):
        print(f"执行测试任务: {task.id} - {task.name}")
        for i in range(10):
            if task.status == "cancelled":
                print(f"任务已取消: {task.id}")
                return
            
            progress = (i + 1) * 10
            task_manager.update_task_progress(task.id, progress, {"step": i + 1})
            print(f"任务进度: {task.id} - {progress}%")
            time.sleep(0.5)
        
        task_manager.complete_task(task.id, {"result": "success"})
    
    # 注册任务处理器
    task_manager.register_task_handler("test", test_task_handler)
    
    # 启动任务管理器
    task_manager.start()
    
    # 创建任务
    task_id = task_manager.create_task("测试任务", "test", {"param": "value"})
    print(f"创建任务: {task_id}")
    
    # 等待任务完成
    time.sleep(6)
    
    # 获取任务
    task = task_manager.get_task(task_id)
    print(f"任务状态: {task.status}, 进度: {task.progress}%, 结果: {task.result}")
    
    # 停止任务管理器
    task_manager.stop()
    
    print("任务管理模块测试完成")