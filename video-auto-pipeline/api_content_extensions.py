#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容管理API扩展
为Web应用添加内容查看和管理的API端点
"""

from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

def register_content_apis(app):
    """注册内容管理相关的API端点"""
    
    @app.route('/api/content/statistics')
    def api_content_statistics():
        """API: 获取内容统计"""
        try:
            from content_storage import content_storage
            stats = content_storage.get_content_statistics()
            return jsonify({'success': True, 'statistics': stats})
        except Exception as e:
            logger.error(f"获取内容统计失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/search')
    def api_content_search():
        """API: 搜索内容"""
        try:
            keyword = request.args.get('keyword', '')
            limit = int(request.args.get('limit', 50))
            
            if not keyword:
                return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
            
            from content_storage import content_storage
            articles = content_storage.search_articles(keyword, limit)
            
            return jsonify({
                'success': True,
                'articles': articles,
                'count': len(articles),
                'keyword': keyword
            })
        except Exception as e:
            logger.error(f"搜索内容失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/categories')
    def api_content_categories():
        """API: 获取内容分类"""
        try:
            from content_storage import content_storage
            categories = content_storage.get_categories()
            return jsonify({'success': True, 'categories': categories})
        except Exception as e:
            logger.error(f"获取内容分类失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/tags')
    def api_content_tags():
        """API: 获取热门标签"""
        try:
            limit = int(request.args.get('limit', 20))
            
            from content_storage import content_storage
            tags = content_storage.get_popular_tags(limit)
            return jsonify({'success': True, 'tags': tags})
        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/task/<task_id>')
    def api_content_by_task(task_id):
        """API: 根据任务ID获取采集的内容"""
        try:
            from content_storage import content_storage
            articles = content_storage.get_articles_by_task(task_id)
            
            return jsonify({
                'success': True,
                'task_id': task_id,
                'articles': articles,
                'count': len(articles)
            })
        except Exception as e:
            logger.error(f"获取任务内容失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/article/<article_id>')
    def api_article_detail(article_id):
        """API: 获取文章详情"""
        try:
            from content_storage import content_storage
            article = content_storage.get_article_by_id(article_id)
            
            if article:
                return jsonify({'success': True, 'article': article})
            else:
                return jsonify({'success': False, 'error': '文章不存在'}), 404
        except Exception as e:
            logger.error(f"获取文章详情失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/article/<article_id>/status', methods=['PUT'])
    def api_update_article_status(article_id):
        """API: 更新文章状态"""
        try:
            data = request.get_json()
            status = data.get('status')
            
            if not status:
                return jsonify({'success': False, 'error': '状态不能为空'}), 400
            
            from content_storage import content_storage
            success = content_storage.update_article_status(article_id, status)
            
            if success:
                return jsonify({'success': True, 'message': '状态更新成功'})
            else:
                return jsonify({'success': False, 'error': '更新失败'}), 400
        except Exception as e:
            logger.error(f"更新文章状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/article/<article_id>', methods=['DELETE'])
    def api_delete_article(article_id):
        """API: 删除文章"""
        try:
            from content_storage import content_storage
            success = content_storage.delete_article(article_id)
            
            if success:
                return jsonify({'success': True, 'message': '文章删除成功'})
            else:
                return jsonify({'success': False, 'error': '删除失败'}), 400
        except Exception as e:
            logger.error(f"删除文章失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tasks/<task_id>/content')
    @app.route('/api/tasks/<task_id>/content')
    def api_task_content_summary(task_id):
        """API: 获取任务的内容摘要"""
        try:
            from content_storage import content_storage
            from task_manager import TaskManager
            
            # 获取任务信息
            task_manager = TaskManager()
            task = task_manager.get_task(task_id)
            
            if not task:
                return jsonify({'success': False, 'error': '任务不存在'}), 404
            
            # 获取任务相关的内容
            articles = content_storage.get_articles_by_task(task_id)
            
            # 生成摘要
            summary = {
                'task_id': task_id,
                'task_name': task.get('name', ''),
                'task_type': task.get('task_type', ''),
                'task_status': task.get('status', ''),
                'articles_count': len(articles),
                'articles': articles[:5],  # 只返回前5篇作为预览
                'total_words': sum(article.get('word_count', 0) for article in articles),
                'categories': list(set(article.get('category', '未分类') for article in articles)),
                'sources': list(set(article.get('source', '') for article in articles if article.get('source')))
            }
            
            return jsonify({'success': True, 'summary': summary})
        except Exception as e:
            logger.error(f"获取任务内容摘要失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/batch-process', methods=['POST'])
    def api_batch_process():
        """API: 批量处理内容"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            process_type = data.get('type')
            content_ids = data.get('content_ids', [])
            params = {k: v for k, v in data.items() if k not in ['type', 'content_ids']}
            
            if not process_type:
                return jsonify({'success': False, 'error': '处理类型不能为空'}), 400
            
            if not content_ids:
                return jsonify({'success': False, 'error': '内容ID列表不能为空'}), 400
            
            # 创建批量处理任务
            from content_processor import content_processor
            task_id = content_processor.create_batch_task(content_ids, process_type, params)
            
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': f'批量{process_type}任务已创建',
                'content_count': len(content_ids)
            })
            
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/batch-process/<task_id>')
    def api_batch_process_status(task_id):
        """API: 获取批量处理任务状态"""
        try:
            from content_processor import content_processor
            task_info = content_processor.get_task_status(task_id)
            
            if not task_info:
                return jsonify({'success': False, 'error': '任务不存在'}), 404
            
            return jsonify({'success': True, 'task': task_info})
            
        except Exception as e:
            logger.error(f"获取批量处理状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/content/processing-tasks')
    def api_processing_tasks():
        """API: 获取所有处理任务"""
        try:
            from content_processor import content_processor
            tasks = content_processor.get_all_tasks()
            
            return jsonify({'success': True, 'tasks': tasks})
            
        except Exception as e:
            logger.error(f"获取处理任务列表失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

def register_content_pages(app):
    """注册内容查看页面"""
    
    @app.route('/content/view/<task_id>')
    def content_view_by_task(task_id):
        """查看特定任务的采集内容"""
        try:
            from content_storage import content_storage
            from task_manager import TaskManager
            
            # 获取任务信息
            task_manager = TaskManager()
            task = task_manager.get_task(task_id)
            
            if not task:
                return "任务不存在", 404
            
            # 获取任务相关的内容
            articles = content_storage.get_articles_by_task(task_id)
            
            # 获取统计信息
            stats = {
                'total_articles': len(articles),
                'total_words': sum(article.get('word_count', 0) for article in articles),
                'categories': list(set(article.get('category', '未分类') for article in articles)),
                'sources': list(set(article.get('source', '') for article in articles if article.get('source')))
            }
            
            return app.jinja_env.get_template('content_view.html').render(
                task=task,
                articles=articles,
                stats=stats
            )
        except Exception as e:
            logger.error(f"内容查看页面加载错误: {e}")
            return f"页面加载错误: {str(e)}", 500
    
    @app.route('/content/article/<article_id>')
    def article_detail_page(article_id):
        """文章详情页面"""
        try:
            from content_storage import content_storage
            
            article = content_storage.get_article_by_id(article_id)
            
            if not article:
                return "文章不存在", 404
            
            return app.jinja_env.get_template('article_detail.html').render(
                article=article
            )
        except Exception as e:
            logger.error(f"文章详情页面加载错误: {e}")
            return f"页面加载错误: {str(e)}", 500