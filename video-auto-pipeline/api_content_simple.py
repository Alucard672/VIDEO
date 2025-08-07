#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容API简化版
提供内容相关的API接口和页面
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import logging
import json
import os
from datetime import datetime
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 内容API蓝图
content_api_bp = Blueprint('content_api', __name__)

# 内容页面蓝图
content_page_bp = Blueprint('content_page', __name__)

def get_content_stats():
    """获取内容统计信息"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总内容数
        cursor.execute("SELECT COUNT(*) FROM content")
        total_articles = cursor.fetchone()[0]
        
        # 已处理内容数
        cursor.execute("SELECT COUNT(*) FROM content WHERE status = 'processed'")
        processed_articles = cursor.fetchone()[0]
        
        # 原始内容数
        cursor.execute("SELECT COUNT(*) FROM content WHERE status = 'raw' OR status IS NULL")
        raw_articles = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_articles': total_articles,
            'processed_articles': processed_articles,
            'raw_articles': raw_articles
        }
        
    except Exception as e:
        logger.error(f"获取内容统计失败: {e}")
        return {
            'total_articles': 0,
            'processed_articles': 0,
            'raw_articles': 0
        }

def register_content_apis(app):
    """注册内容API"""
    app.register_blueprint(content_api_bp, url_prefix='/api/content')
    logger.info("内容API已注册")

def register_content_pages(app):
    """注册内容页面"""
    app.register_blueprint(content_page_bp, url_prefix='/content')
    logger.info("内容页面已注册")

# API路由
@content_api_bp.route('/')
def api_content():
    """获取内容列表API - 主路由"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        category = request.args.get('category')
        task_id = request.args.get('task_id')
        
        # 从数据库获取内容
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
            SELECT id, title, content, category, tags, source_url, created_at, 
                   task_id, source_id, status, word_count, summary, author, publish_time
            FROM content
        '''
        params = []
        conditions = []
        
        if category:
            conditions.append("category = ?")
            params.append(category)
            
        if task_id:
            conditions.append("task_id = ?")
            params.append(task_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM content"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
            cursor.execute(count_query, params[:-2])  # 排除limit和offset参数
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()[0]
        
        # 构建结果
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1] or '无标题',
                'content': row[2] or '',
                'category': row[3] or '未分类',
                'tags': json.loads(row[4]) if row[4] else [],
                'source_url': row[5],
                'created_time': row[6],
                'task_id': row[7],
                'task_name': f'任务{row[7]}' if row[7] else None,
                'source_id': row[8],
                'source': f'来源{row[8]}' if row[8] else None,
                'status': row[9] or 'raw',
                'word_count': row[10] or len(row[2] or ''),
                'summary': row[11] or (row[2][:100] + '...' if row[2] and len(row[2]) > 100 else row[2]),
                'author': row[12],
                'publish_time': row[13]
            })
        
        conn.close()
        
        # 获取统计信息
        stats = get_content_stats()
        
        return jsonify({
            'success': True,
            'content': results,
            'total': total,
            'page': page,
            'limit': limit,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@content_api_bp.route('/list')
def api_content_list():
    """获取内容列表API"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        category = request.args.get('category')
        
        # 从数据库获取内容
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询 - 使用实际的数据库字段
        query = "SELECT id, title, description, content_type, tags, created_at FROM content"
        params = []
        
        if category:
            query += " WHERE content_type = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM content"
        if category:
            count_query += " WHERE content_type = ?"
            cursor.execute(count_query, [category])
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()[0]
        
        # 构建结果
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3],
                'tags': json.loads(row[4]) if row[4] else [],
                'created_at': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'total': total,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_api_bp.route('/task/<task_id>')
def api_content_by_task(task_id):
    """根据任务ID获取内容"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, tags, source_url, created_at, 
                   task_id, source_id, status, word_count, summary, author, publish_time
            FROM content
            WHERE task_id = ?
            ORDER BY created_at DESC
        ''', [task_id])
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1] or '无标题',
                'content': row[2] or '',
                'category': row[3] or '未分类',
                'tags': json.loads(row[4]) if row[4] else [],
                'source_url': row[5],
                'created_time': row[6],
                'task_id': row[7],
                'source_id': row[8],
                'status': row[9] or 'raw',
                'word_count': row[10] or len(row[2] or ''),
                'summary': row[11] or (row[2][:100] + '...' if row[2] and len(row[2]) > 100 else row[2]),
                'author': row[12],
                'publish_time': row[13]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'articles': results
        })
        
    except Exception as e:
        logger.error(f"根据任务获取内容失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@content_api_bp.route('/article/<article_id>')
def api_article_detail(article_id):
    """获取文章详情"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, tags, source_url, created_at, 
                   task_id, source_id, status, word_count, summary, author, publish_time
            FROM content
            WHERE id = ?
        ''', [article_id])
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': '文章不存在'})
        
        result = {
            'id': row[0],
            'title': row[1] or '无标题',
            'content': row[2] or '',
            'category': row[3] or '未分类',
            'tags': json.loads(row[4]) if row[4] else [],
            'source_url': row[5],
            'created_time': row[6],
            'task_id': row[7],
            'source_id': row[8],
            'status': row[9] or 'raw',
            'word_count': row[10] or len(row[2] or ''),
            'summary': row[11] or (row[2][:100] + '...' if row[2] and len(row[2]) > 100 else row[2]),
            'author': row[12],
            'publish_time': row[13]
        }
        
        return jsonify({
            'success': True,
            'article': result
        })
        
    except Exception as e:
        logger.error(f"获取文章详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@content_api_bp.route('/article/<article_id>', methods=['DELETE'])
def api_delete_article(article_id):
    """删除文章"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM content WHERE id = ?', [article_id])
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': '文章已删除'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': '文章不存在'})
        
    except Exception as e:
        logger.error(f"删除文章失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@content_api_bp.route('/batch-process', methods=['POST'])
def api_batch_process():
    """批量处理内容"""
    try:
        data = request.get_json()
        process_type = data.get('type')
        content_ids = data.get('content_ids', [])
        
        if not process_type or not content_ids:
            return jsonify({'success': False, 'error': '参数不完整'})
        
        # 这里可以添加实际的批量处理逻辑
        # 目前返回一个模拟的任务ID
        task_id = f"batch_{process_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'批量{process_type}任务已创建'
        })
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@content_api_bp.route('/<int:content_id>')
def api_content_detail(content_id):
    """获取内容详情API"""
    try:
        # 从数据库获取内容
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, tags, source_url, created_at
            FROM content
            WHERE id = ?
        ''', [content_id])
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'message': '内容不存在'})
        
        # 构建结果
        result = {
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'category': row[3],
            'tags': json.loads(row[4]) if row[4] else [],
            'source_url': row[5],
            'created_at': row[6]
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"获取内容详情失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_api_bp.route('/categories')
def api_content_categories():
    """获取内容分类API"""
    try:
        # 从配置获取分类
        from content_fetch_config import ContentFetchConfig
        config = ContentFetchConfig()
        categories = config.get_categories()
        
        return jsonify({'success': True, 'data': categories})
        
    except Exception as e:
        logger.error(f"获取内容分类失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_api_bp.route('/search')
def api_content_search():
    """搜索内容API"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        if not keyword:
            return jsonify({'success': False, 'message': '关键词不能为空'})
        
        # 从数据库搜索内容
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
            SELECT id, title, content, category, tags, source_url, created_at
            FROM content
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        
        search_param = f"%{keyword}%"
        cursor.execute(query, [search_param, search_param, limit, (page - 1) * limit])
        
        # 获取结果
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],  # 截断内容
                'category': row[3],
                'tags': json.loads(row[4]) if row[4] else [],
                'source_url': row[5],
                'created_at': row[6]
            })
        
        # 获取总数
        cursor.execute('''
            SELECT COUNT(*)
            FROM content
            WHERE title LIKE ? OR content LIKE ?
        ''', [search_param, search_param])
        
        total = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'total': total,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"搜索内容失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@content_api_bp.route('/stats')
def api_content_stats():
    """获取内容统计API"""
    try:
        # 从数据库获取统计
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总内容数
        cursor.execute("SELECT COUNT(*) FROM content")
        total_count = cursor.fetchone()[0]
        
        # 分类统计 - 使用category字段
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM content
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        category_stats = []
        for row in cursor.fetchall():
            category_stats.append({
                'category': row[0] or '未分类',
                'count': row[1]
            })
        
        # 来源统计
        cursor.execute('''
            SELECT source_id, COUNT(*) as count
            FROM content
            GROUP BY source_id
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        source_stats = []
        for row in cursor.fetchall():
            source_stats.append({
                'source_id': row[0],
                'count': row[1]
            })
        
        # 日期统计
        cursor.execute('''
            SELECT substr(created_at, 1, 10) as date, COUNT(*) as count
            FROM content
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        date_stats = []
        for row in cursor.fetchall():
            date_stats.append({
                'date': row[0],
                'count': row[1]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_count': total_count,
                'category_stats': category_stats,
                'source_stats': source_stats,
                'date_stats': date_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取内容统计失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

# 页面路由
@content_page_bp.route('/')
def content_list_page():
    """内容列表页面"""
    try:
        # 获取查询参数
        category = request.args.get('category')
        
        # 获取分类
        try:
            from content_fetch_config import ContentFetchConfig
            config = ContentFetchConfig()
            categories = config.get_categories()
        except:
            categories = []
        
        # 获取统计数据
        stats = get_content_stats()
        
        return render_template(
            'content.html',
            title="内容管理",
            category=category,
            categories=categories,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"加载内容列表页面失败: {e}")
        return render_template('error.html', error=str(e))

@content_page_bp.route('/view/<int:content_id>')
def content_view_page(content_id):
    """内容查看页面"""
    try:
        # 从数据库获取内容
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, tags, source_url, created_at
            FROM content
            WHERE id = ?
        ''', [content_id])
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return render_template('404.html', title="内容不存在")
        
        # 构建结果
        content = {
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'category': row[3],
            'tags': json.loads(row[4]) if row[4] else [],
            'source_url': row[5],
            'created_at': row[6]
        }
        
        return render_template(
            'content_view.html',
            title=content['title'],
            content=content
        )
        
    except Exception as e:
        logger.error(f"加载内容查看页面失败: {e}")
        return render_template('error.html', error=str(e))

@content_page_bp.route('/search')
def content_search_page():
    """内容搜索页面"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '')
        
        return render_template(
            'content.html',
            title="内容搜索",
            keyword=keyword,
            is_search=True
        )
        
    except Exception as e:
        logger.error(f"加载内容搜索页面失败: {e}")
        return render_template('error.html', error=str(e))

@content_page_bp.route('/article/<int:content_id>')
def article_detail_page(content_id):
    """文章详情页面"""
    try:
        # 从数据库获取内容
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, tags, source_url, created_at
            FROM content
            WHERE id = ?
        ''', [content_id])
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return render_template('404.html', title="文章不存在")
        
        # 构建结果
        article = {
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'category': row[3],
            'tags': json.loads(row[4]) if row[4] else [],
            'source_url': row[5],
            'created_at': row[6]
        }
        
        # 获取相关文章
        cursor.execute('''
            SELECT id, title, category, created_at
            FROM content
            WHERE category = ? AND id != ?
            ORDER BY created_at DESC
            LIMIT 5
        ''', [article['category'], content_id])
        
        related_articles = []
        for row in cursor.fetchall():
            related_articles.append({
                'id': row[0],
                'title': row[1],
                'category': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        return render_template(
            'article_detail.html',
            title=article['title'],
            article=article,
            related_articles=related_articles
        )
        
    except Exception as e:
        logger.error(f"加载文章详情页面失败: {e}")
        return render_template('error.html', error=str(e))

# 测试代码
if __name__ == "__main__":
    from flask import Flask
    
    app = Flask(__name__)
    register_content_apis(app)
    register_content_pages(app)
    
    app.run(debug=True)