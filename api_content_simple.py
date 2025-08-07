#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的内容管理API扩展
"""

import logging
from flask import jsonify, request

logger = logging.getLogger(__name__)

def register_content_apis(app):
    """注册内容管理API"""
    
    @app.route('/api/content')
    def api_get_content():
        """API: 获取内容列表"""
        try:
            # 直接导入修复后的content_storage
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent
            sys.path.insert(0, str(project_root))
            
            from content_storage import content_storage
            
            # 获取查询参数
            category = request.args.get('category')
            source = request.args.get('source')
            status = request.args.get('status')
            task_id = request.args.get('task_id')
            limit = int(request.args.get('limit', 50))
            
            # 获取内容
            if task_id:
                articles = content_storage.get_articles_by_task(task_id)
            else:
                articles = content_storage.get_recent_articles(
                    limit=limit, 
                    category=category, 
                    status=status
                )
            
            # 如果指定了来源，进行过滤
            if source:
                articles = [a for a in articles if a.get('source') == source]
            
            return jsonify({
                'success': True,
                'content': articles,
                'total': len(articles)
            })
            
        except Exception as e:
            logger.error(f"获取内容列表失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'content': []
            }), 500
    
    @app.route('/api/content/statistics')
    def api_content_statistics():
        """API: 获取内容统计"""
        try:
            from content_storage import content_storage
            stats = content_storage.get_content_statistics()
            
            return jsonify({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"获取内容统计失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/content/task/<task_id>')
    def api_task_content(task_id):
        """API: 获取任务的内容"""
        try:
            from content_storage import content_storage
            articles = content_storage.get_articles_by_task(task_id)
            
            return jsonify({
                'success': True,
                'articles': articles,
                'count': len(articles)
            })
            
        except Exception as e:
            logger.error(f"获取任务内容失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'articles': []
            }), 500

def register_content_pages(app):
    """注册内容管理页面"""
    
    @app.route('/content')
    def content_management():
        """内容管理页面"""
        try:
            from content_storage import content_storage
            stats = content_storage.get_content_statistics()
            
            return app.jinja_env.get_template('content.html').render(
                stats=stats.get('total_stats', {})
            )
            
        except Exception as e:
            logger.error(f"渲染内容管理页面失败: {e}")
            return f"页面加载失败: {e}", 500
    
    @app.route('/content/view/<task_id>')
    def view_task_content(task_id):
        """查看任务内容页面"""
        try:
            from content_storage import content_storage
            from task_manager import TaskManager
            
            # 获取任务信息
            task_manager = TaskManager()
            task = task_manager.get_task(task_id)
            
            # 获取任务内容
            articles = content_storage.get_articles_by_task(task_id)
            
            return app.jinja_env.get_template('content_view.html').render(
                task=task,
                articles=articles
            )
            
        except Exception as e:
            logger.error(f"渲染任务内容页面失败: {e}")
            return f"页面加载失败: {e}", 500
    
    @app.route('/content/article/<article_id>')
    def view_article_detail(article_id):
        """查看文章详情页面"""
        try:
            from content_storage import content_storage
            
            # 获取文章详情
            article = content_storage.get_article_by_id(article_id)
            
            if not article:
                return "文章不存在", 404
            
            return app.jinja_env.get_template('article_detail.html').render(
                article=article
            )
            
        except Exception as e:
            logger.error(f"渲染文章详情页面失败: {e}")
            return f"页面加载失败: {e}", 500

if __name__ == "__main__":
    print("内容管理API扩展模块")