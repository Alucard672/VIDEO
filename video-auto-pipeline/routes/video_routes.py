#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频管理路由
提供视频相关的API接口
"""

from flask import Blueprint, request, jsonify
import logging
import json
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

# 创建视频路由蓝图
video_bp = Blueprint('video', __name__, url_prefix='/api/videos')

@video_bp.route('/', methods=['GET'])
def get_videos():
    """获取视频列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        category = request.args.get('category')
        status = request.args.get('status')
        
        # 从数据库获取视频数据
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
            SELECT id, title, description, video_url, thumbnail_url, duration, 
                   category, tags, status, created_at, updated_at, view_count,
                   like_count, comment_count, source_platform, source_id
            FROM videos
        '''
        params = []
        conditions = []
        
        if category:
            conditions.append("category = ?")
            params.append(category)
            
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM videos"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
            cursor.execute(count_query, params[:-2])  # 排除limit和offset参数
        else:
            cursor.execute(count_query)
        
        total = cursor.fetchone()[0]
        
        # 构建结果
        videos = []
        for row in rows:
            # 安全处理tags字段
            tags = []
            if row[7]:
                try:
                    if row[7].startswith('['):
                        tags = json.loads(row[7])
                    else:
                        tags = [tag.strip() for tag in row[7].split(',') if tag.strip()]
                except:
                    tags = [row[7]]
            
            videos.append({
                'id': row[0],
                'title': row[1] or '无标题',
                'description': row[2] or '',
                'video_url': row[3],
                'thumbnail_url': row[4] or '/static/images/default-thumbnail.svg',
                'duration': row[5],
                'category': row[6] or '未分类',
                'tags': tags,
                'status': row[8] or 'draft',
                'created_at': row[9],
                'updated_at': row[10],
                'view_count': row[11] or 0,
                'like_count': row[12] or 0,
                'comment_count': row[13] or 0,
                'source_platform': row[14],
                'source_id': row[15]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': total,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"获取视频列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/statistics', methods=['GET'])
def get_video_statistics():
    """获取视频统计信息"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总视频数
        cursor.execute("SELECT COUNT(*) FROM videos")
        total_videos = cursor.fetchone()[0]
        
        # 已发布视频数
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'published'")
        published_videos = cursor.fetchone()[0]
        
        # 草稿视频数
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'draft'")
        draft_videos = cursor.fetchone()[0]
        
        # 处理中视频数
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'processing'")
        processing_videos = cursor.fetchone()[0]
        
        # 总观看数
        cursor.execute("SELECT SUM(view_count) FROM videos")
        total_views = cursor.fetchone()[0] or 0
        
        # 总点赞数
        cursor.execute("SELECT SUM(like_count) FROM videos")
        total_likes = cursor.fetchone()[0] or 0
        
        # 分类统计
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM videos
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        category_stats = []
        for row in cursor.fetchall():
            category_stats.append({
                'category': row[0] or '未分类',
                'count': row[1]
            })
        
        # 平台统计
        cursor.execute('''
            SELECT source_platform, COUNT(*) as count
            FROM videos
            GROUP BY source_platform
            ORDER BY count DESC
        ''')
        
        platform_stats = []
        for row in cursor.fetchall():
            platform_stats.append({
                'platform': row[0] or '未知',
                'count': row[1]
            })
        
        # 最近7天的视频创建统计
        cursor.execute('''
            SELECT substr(created_at, 1, 10) as date, COUNT(*) as count
            FROM videos
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY date
            ORDER BY date DESC
        ''')
        
        recent_stats = []
        for row in cursor.fetchall():
            recent_stats.append({
                'date': row[0],
                'count': row[1]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_videos': total_videos,
                'published_videos': published_videos,
                'draft_videos': draft_videos,
                'processing_videos': processing_videos,
                'total_views': total_views,
                'total_likes': total_likes,
                'category_stats': category_stats,
                'platform_stats': platform_stats,
                'recent_stats': recent_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取视频统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/<int:video_id>', methods=['GET'])
def get_video_detail(video_id):
    """获取视频详情"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, video_url, thumbnail_url, duration, 
                   category, tags, status, created_at, updated_at, view_count,
                   like_count, comment_count, source_platform, source_id
            FROM videos
            WHERE id = ?
        ''', [video_id])
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': '视频不存在'}), 404
        
        # 安全处理tags字段
        tags = []
        if row[7]:
            try:
                if row[7].startswith('['):
                    tags = json.loads(row[7])
                else:
                    tags = [tag.strip() for tag in row[7].split(',') if tag.strip()]
            except:
                tags = [row[7]]
        
        video = {
            'id': row[0],
            'title': row[1] or '无标题',
            'description': row[2] or '',
            'video_url': row[3],
            'thumbnail_url': row[4] or '/static/images/default-thumbnail.jpg',
            'duration': row[5],
            'category': row[6] or '未分类',
            'tags': tags,
            'status': row[8] or 'draft',
            'created_at': row[9],
            'updated_at': row[10],
            'view_count': row[11] or 0,
            'like_count': row[12] or 0,
            'comment_count': row[13] or 0,
            'source_platform': row[14],
            'source_id': row[15]
        }
        
        return jsonify({
            'success': True,
            'video': video
        })
        
    except Exception as e:
        logger.error(f"获取视频详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/', methods=['POST'])
def create_video():
    """创建新视频"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        # 验证必需字段
        required_fields = ['title']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400
        
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 插入新视频
        cursor.execute('''
            INSERT INTO videos (
                title, description, video_url, thumbnail_url, duration,
                category, tags, status, created_at, updated_at,
                source_platform, source_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            data.get('title'),
            data.get('description', ''),
            data.get('video_url'),
            data.get('thumbnail_url'),
            data.get('duration'),
            data.get('category', '未分类'),
            json.dumps(data.get('tags', [])),
            data.get('status', 'draft'),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            data.get('source_platform'),
            data.get('source_id')
        ])
        
        video_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'message': '视频创建成功'
        })
        
    except Exception as e:
        logger.error(f"创建视频失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/<int:video_id>', methods=['PUT'])
def update_video(video_id):
    """更新视频信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查视频是否存在
        cursor.execute('SELECT id FROM videos WHERE id = ?', [video_id])
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': '视频不存在'}), 404
        
        # 构建更新字段
        update_fields = []
        params = []
        
        for field in ['title', 'description', 'video_url', 'thumbnail_url', 'duration', 'category', 'status', 'source_platform', 'source_id']:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if 'tags' in data:
            update_fields.append("tags = ?")
            params.append(json.dumps(data['tags']))
        
        if update_fields:
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(video_id)
            
            query = f"UPDATE videos SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '视频更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新视频失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    """删除视频"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM videos WHERE id = ?', [video_id])
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': '视频已删除'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': '视频不存在'}), 404
        
    except Exception as e:
        logger.error(f"删除视频失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/batch', methods=['POST'])
def batch_operation():
    """批量操作视频"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        operation = data.get('operation')
        video_ids = data.get('video_ids', [])
        
        if not operation or not video_ids:
            return jsonify({'success': False, 'error': '参数不完整'}), 400
        
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        success_count = 0
        
        if operation == 'delete':
            # 批量删除
            for video_id in video_ids:
                cursor.execute('DELETE FROM videos WHERE id = ?', [video_id])
                if cursor.rowcount > 0:
                    success_count += 1
        
        elif operation == 'update_status':
            # 批量更新状态
            new_status = data.get('status', 'draft')
            for video_id in video_ids:
                cursor.execute(
                    'UPDATE videos SET status = ?, updated_at = ? WHERE id = ?',
                    [new_status, datetime.now().isoformat(), video_id]
                )
                if cursor.rowcount > 0:
                    success_count += 1
        
        elif operation == 'update_category':
            # 批量更新分类
            new_category = data.get('category', '未分类')
            for video_id in video_ids:
                cursor.execute(
                    'UPDATE videos SET category = ?, updated_at = ? WHERE id = ?',
                    [new_category, datetime.now().isoformat(), video_id]
                )
                if cursor.rowcount > 0:
                    success_count += 1
        
        else:
            conn.close()
            return jsonify({'success': False, 'error': '不支持的操作'}), 400
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'批量操作完成，成功处理 {success_count} 个视频'
        })
        
    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/categories', methods=['GET'])
def get_video_categories():
    """获取视频分类列表"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM videos
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'name': row[0] or '未分类',
                'count': row[1]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"获取视频分类失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@video_bp.route('/search', methods=['GET'])
def search_videos():
    """搜索视频"""
    try:
        keyword = request.args.get('keyword', '')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        if not keyword:
            return jsonify({'success': False, 'error': '关键词不能为空'}), 400
        
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 搜索查询
        search_param = f"%{keyword}%"
        query = '''
            SELECT id, title, description, video_url, thumbnail_url, duration, 
                   category, tags, status, created_at, updated_at, view_count,
                   like_count, comment_count, source_platform, source_id
            FROM videos
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        
        cursor.execute(query, [search_param, search_param, limit, (page - 1) * limit])
        rows = cursor.fetchall()
        
        # 获取总数
        cursor.execute('''
            SELECT COUNT(*)
            FROM videos
            WHERE title LIKE ? OR description LIKE ?
        ''', [search_param, search_param])
        
        total = cursor.fetchone()[0]
        
        # 构建结果
        videos = []
        for row in rows:
            # 安全处理tags字段
            tags = []
            if row[7]:
                try:
                    if row[7].startswith('['):
                        tags = json.loads(row[7])
                    else:
                        tags = [tag.strip() for tag in row[7].split(',') if tag.strip()]
                except:
                    tags = [row[7]]
            
            videos.append({
                'id': row[0],
                'title': row[1] or '无标题',
                'description': row[2] or '',
                'video_url': row[3],
                'thumbnail_url': row[4] or '/static/images/default-thumbnail.svg',
                'duration': row[5],
                'category': row[6] or '未分类',
                'tags': tags,
                'status': row[8] or 'draft',
                'created_at': row[9],
                'updated_at': row[10],
                'view_count': row[11] or 0,
                'like_count': row[12] or 0,
                'comment_count': row[13] or 0,
                'source_platform': row[14],
                'source_id': row[15]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': total,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"搜索视频失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500