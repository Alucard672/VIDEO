from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import threading
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from content_fetch_config import ContentFetchConfig

try:
    # 使用相对路径导入
    content_fetch_path = Path(__file__).parent.parent / "content_fetch"
    sys.path.append(str(content_fetch_path))
    from enhanced_fetcher import EnhancedContentFetcher
except ImportError as e:
    print(f"导入EnhancedContentFetcher失败: {e}")
    # 创建一个简单的替代实现
    class EnhancedContentFetcher:
        def fetch_from_source(self, source, limit=10):
            return [{'title': f'测试内容{i}', 'content': f'这是测试内容{i}', 'url': source.get('url', ''), 'category': source.get('category', '')} for i in range(min(limit, 3))]
from database import get_db_connection

content_fetch_bp = Blueprint('content_fetch', __name__)

# 全局变量存储运行中的任务
running_tasks = {}
task_threads = {}

@content_fetch_bp.route('/content-fetch')
def content_fetch_page():
    """内容采集管理页面"""
    try:
        config = ContentFetchConfig()
        
        # 获取采集源
        sources = config.get_sources()
        enabled_sources = len([s for s in sources if s.get('enabled', True)])
        
        # 获取分类
        categories = config.get_categories()
        
        # 获取任务
        tasks = get_fetch_tasks()
        running_tasks_count = len([t for t in tasks if t.get('status') == 'running'])
        
        # 统计数据
        platform_stats = {}
        category_stats = {}
        
        for source in sources:
            platform = source.get('platform', 'unknown')
            platform_stats[platform] = platform_stats.get(platform, 0) + 1
            
            category = source.get('category', 'uncategorized')
            category_stats[category] = category_stats.get(category, 0) + 1
        
        return render_template('content_fetch.html',
                             sources=sources,
                             enabled_sources=enabled_sources,
                             categories=categories,
                             tasks=tasks,
                             running_tasks=running_tasks_count,
                             platform_stats=platform_stats,
                             category_stats=category_stats)
    except Exception as e:
        print(f"Error loading content fetch page: {e}")
        return render_template('error.html', error=str(e))

@content_fetch_bp.route('/api/content-fetch/create-task', methods=['POST'])
def create_fetch_task():
    """创建采集任务"""
    try:
        data = request.get_json()
        task_name = data.get('task_name')
        source_filters = data.get('source_filters', [])
        category_filters = data.get('category_filters', [])
        total_limit = data.get('total_limit', 50)
        
        if not task_name:
            return jsonify({'success': False, 'message': '任务名称不能为空'})
        
        if not source_filters:
            return jsonify({'success': False, 'message': '请至少选择一个采集源'})
        
        # 创建任务记录
        task_id = create_task_record(task_name, source_filters, category_filters, total_limit)
        
        return jsonify({
            'success': True,
            'message': '任务创建成功',
            'task_id': task_id
        })
        
    except Exception as e:
        print(f"Error creating fetch task: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/start-task/<int:task_id>', methods=['POST'])
def start_fetch_task(task_id):
    """开始执行采集任务"""
    try:
        if task_id in running_tasks:
            return jsonify({'success': False, 'message': '任务已在运行中'})
        
        # 获取任务信息
        task = get_task_by_id(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'})
        
        if task['status'] != 'pending':
            return jsonify({'success': False, 'message': '任务状态不允许启动'})
        
        # 更新任务状态
        update_task_status(task_id, 'running', 0)
        
        # 在后台线程中执行任务
        thread = threading.Thread(target=execute_fetch_task, args=(task_id, task))
        thread.daemon = True
        thread.start()
        
        task_threads[task_id] = thread
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'start_time': datetime.now(),
            'thread': thread
        }
        
        return jsonify({'success': True, 'message': '任务已开始执行'})
        
    except Exception as e:
        print(f"Error starting fetch task: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/stop-task/<int:task_id>', methods=['POST'])
def stop_fetch_task(task_id):
    """停止采集任务"""
    try:
        if task_id not in running_tasks:
            return jsonify({'success': False, 'message': '任务未在运行'})
        
        # 标记任务为停止状态
        running_tasks[task_id]['status'] = 'stopping'
        update_task_status(task_id, 'stopped', running_tasks[task_id]['progress'])
        
        # 清理运行状态
        if task_id in running_tasks:
            del running_tasks[task_id]
        if task_id in task_threads:
            del task_threads[task_id]
        
        return jsonify({'success': True, 'message': '任务已停止'})
        
    except Exception as e:
        print(f"Error stopping fetch task: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/task-status')
def get_task_status():
    """获取任务状态"""
    try:
        tasks = []
        for task_id, task_info in running_tasks.items():
            tasks.append({
                'id': task_id,
                'status': task_info['status'],
                'progress': task_info['progress'],
                'result_count': task_info.get('result_count', 0)
            })
        
        return jsonify({'success': True, 'tasks': tasks})
        
    except Exception as e:
        print(f"Error getting task status: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/test-source/<int:source_id>', methods=['POST'])
def test_source(source_id):
    """测试采集源"""
    try:
        config = ContentFetchConfig()
        sources = config.get_sources()
        
        source = None
        for s in sources:
            if s.get('id') == source_id:
                source = s
                break
        
        if not source:
            return jsonify({'success': False, 'message': '采集源不存在'})
        
        # 创建采集器并测试
        fetcher = EnhancedContentFetcher()
        results = fetcher.fetch_from_source(source, limit=5)  # 测试采集5条
        
        return jsonify({
            'success': True,
            'message': '测试成功',
            'count': len(results),
            'results': results[:3]  # 返回前3条作为预览
        })
        
    except Exception as e:
        print(f"Error testing source: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/toggle-source/<int:source_id>', methods=['POST'])
def toggle_source(source_id):
    """切换采集源状态"""
    try:
        config = ContentFetchConfig()
        sources = config.get_sources()
        
        for i, source in enumerate(sources):
            if source.get('id') == source_id:
                sources[i]['enabled'] = not source.get('enabled', True)
                config.save_sources(sources)
                return jsonify({'success': True, 'message': '状态更新成功'})
        
        return jsonify({'success': False, 'message': '采集源不存在'})
        
    except Exception as e:
        print(f"Error toggling source: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/add-source', methods=['POST'])
def add_source():
    """添加采集源"""
    try:
        data = request.get_json()
        
        config = ContentFetchConfig()
        sources = config.get_sources()
        
        # 生成新的ID
        max_id = max([s.get('id', 0) for s in sources], default=0)
        new_id = max_id + 1
        
        new_source = {
            'id': new_id,
            'name': data.get('name'),
            'platform': data.get('platform'),
            'url': data.get('url'),
            'description': data.get('description', ''),
            'category': data.get('category'),
            'fetch_limit': data.get('fetch_limit', 20),
            'fetch_interval': data.get('fetch_interval', 60),
            'enabled': True,
            'created_at': datetime.now().isoformat()
        }
        
        sources.append(new_source)
        config.save_sources(sources)
        
        return jsonify({'success': True, 'message': '采集源添加成功'})
        
    except Exception as e:
        print(f"Error adding source: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/delete-task/<int:task_id>', methods=['POST', 'DELETE'])
def delete_task(task_id):
    """删除采集任务"""
    try:
        # 检查任务是否存在
        task = get_task_by_id(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'})
        
        # 如果任务正在运行，先停止它
        if task_id in running_tasks:
            running_tasks[task_id]['status'] = 'stopping'
            if task_id in task_threads:
                del task_threads[task_id]
            del running_tasks[task_id]
        
        # 从数据库中删除任务
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM fetch_tasks WHERE id = ?', (task_id,))
        
        # 可选：删除相关的采集结果
        cursor.execute('DELETE FROM content WHERE task_id = ?', (task_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '任务已删除'})
        
    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/task/<int:task_id>')
def get_task(task_id):
    """获取任务详情"""
    try:
        task = get_task_by_id(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'})
        
        return jsonify({'success': True, 'task': task})
        
    except Exception as e:
        print(f"Error getting task: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_fetch_bp.route('/api/content-fetch/task-results/<int:task_id>')
def get_task_results(task_id):
    """获取任务采集结果"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, tags, source_url, created_at
            FROM content
            WHERE task_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (task_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3],
                'tags': json.loads(row[4]) if row[4] else [],
                'source_url': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        print(f"Error getting task results: {e}")
        return jsonify({'success': False, 'message': str(e)})

def create_task_record(task_name, source_filters, category_filters, total_limit):
    """创建任务记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fetch_tasks (task_name, source_ids, category_filters, total_limit, status, progress, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_name,
            json.dumps(source_filters),
            json.dumps(category_filters),
            total_limit,
            'pending',
            0,
            datetime.now().isoformat()
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
        
    except Exception as e:
        print(f"Error creating task record: {e}")
        # 如果数据库操作失败，创建表
        create_fetch_tasks_table()
        return create_task_record(task_name, source_filters, category_filters, total_limit)

def get_fetch_tasks():
    """获取采集任务列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, task_name, source_ids, category_filters, total_limit, status, progress, result_count, created_at
            FROM fetch_tasks
            ORDER BY created_at DESC
        ''')
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'task_name': row[1],
                'source_ids': json.loads(row[2]) if row[2] else [],
                'category_filters': json.loads(row[3]) if row[3] else [],
                'total_limit': row[4],
                'status': row[5],
                'progress': row[6],
                'result_count': row[7],
                'created_at': row[8]
            })
        
        conn.close()
        return tasks
        
    except Exception as e:
        print(f"Error getting fetch tasks: {e}")
        create_fetch_tasks_table()
        return []

def get_task_by_id(task_id):
    """根据ID获取任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, task_name, source_ids, category_filters, total_limit, status, progress, result_count, created_at
            FROM fetch_tasks
            WHERE id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'task_name': row[1],
                'source_ids': json.loads(row[2]) if row[2] else [],
                'category_filters': json.loads(row[3]) if row[3] else [],
                'total_limit': row[4],
                'status': row[5],
                'progress': row[6],
                'result_count': row[7],
                'created_at': row[8]
            }
        return None
        
    except Exception as e:
        print(f"Error getting task by id: {e}")
        return None

def update_task_status(task_id, status, progress, result_count=None):
    """更新任务状态"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if result_count is not None:
            cursor.execute('''
                UPDATE fetch_tasks 
                SET status = ?, progress = ?, result_count = ?, updated_at = ?
                WHERE id = ?
            ''', (status, progress, result_count, datetime.now().isoformat(), task_id))
        else:
            cursor.execute('''
                UPDATE fetch_tasks 
                SET status = ?, progress = ?, updated_at = ?
                WHERE id = ?
            ''', (status, progress, datetime.now().isoformat(), task_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error updating task status: {e}")

def execute_fetch_task(task_id, task):
    """执行采集任务"""
    try:
        print(f"开始执行采集任务 {task_id}: {task['task_name']}")
        
        config = ContentFetchConfig()
        fetcher = EnhancedContentFetcher()
        
        # 获取要采集的源
        all_sources = config.get_sources()
        target_sources = []
        
        for source in all_sources:
            if str(source.get('id')) in task['source_ids'] and source.get('enabled', True):
                target_sources.append(source)
        
        if not target_sources:
            update_task_status(task_id, 'failed', 0, 0)
            if task_id in running_tasks:
                del running_tasks[task_id]
            return
        
        total_collected = 0
        total_limit = task['total_limit']
        
        for i, source in enumerate(target_sources):
            if task_id in running_tasks and running_tasks[task_id]['status'] == 'stopping':
                break
            
            try:
                # 计算这个源应该采集多少条
                remaining_limit = total_limit - total_collected
                source_limit = min(source.get('fetch_limit', 20), remaining_limit)
                
                if source_limit <= 0:
                    break
                
                print(f"从 {source['name']} 采集 {source_limit} 条内容...")
                
                # 执行采集
                results = fetcher.fetch_from_source(source, limit=source_limit)
                
                if results:
                    # 过滤分类
                    if task['category_filters']:
                        filtered_results = []
                        for result in results:
                            if result.get('category') in task['category_filters']:
                                filtered_results.append(result)
                        results = filtered_results
                    
                    # 保存结果
                    save_fetch_results(task_id, source['id'], results)
                    total_collected += len(results)
                    
                    print(f"从 {source['name']} 成功采集 {len(results)} 条内容")
                
                # 更新进度
                progress = int((i + 1) / len(target_sources) * 100)
                if task_id in running_tasks:
                    running_tasks[task_id]['progress'] = progress
                    running_tasks[task_id]['result_count'] = total_collected
                
                update_task_status(task_id, 'running', progress, total_collected)
                
                # 检查是否达到总限制
                if total_collected >= total_limit:
                    break
                
                # 采集间隔
                time.sleep(2)
                
            except Exception as e:
                print(f"采集源 {source['name']} 出错: {e}")
                continue
        
        # 任务完成
        final_status = 'completed' if total_collected > 0 else 'failed'
        update_task_status(task_id, final_status, 100, total_collected)
        
        if task_id in running_tasks:
            del running_tasks[task_id]
        if task_id in task_threads:
            del task_threads[task_id]
        
        print(f"采集任务 {task_id} 完成，共采集 {total_collected} 条内容")
        
    except Exception as e:
        print(f"执行采集任务出错: {e}")
        update_task_status(task_id, 'failed', 0, 0)
        if task_id in running_tasks:
            del running_tasks[task_id]
        if task_id in task_threads:
            del task_threads[task_id]

def save_fetch_results(task_id, source_id, results):
    """保存采集结果"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute('''
                INSERT OR REPLACE INTO content (
                    title, content, category, tags, source_url, 
                    created_at, task_id, source_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('title', ''),
                result.get('content', ''),
                result.get('category', ''),
                json.dumps(result.get('tags', [])),
                result.get('url', ''),
                datetime.now().isoformat(),
                task_id,
                source_id
            ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error saving fetch results: {e}")

def create_fetch_tasks_table():
    """创建采集任务表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error creating fetch_tasks table: {e}")