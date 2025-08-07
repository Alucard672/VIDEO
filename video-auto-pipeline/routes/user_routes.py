from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from user_manager import UserManager
import logging

logger = logging.getLogger(__name__)

# 创建用户蓝图
user_bp = Blueprint('user', __name__)

# 初始化用户管理器
try:
    user_manager = UserManager()
except Exception as e:
    logger.error(f"初始化用户管理器失败: {e}")
    user_manager = None

@user_bp.route('/users')
def users():
    """用户列表页面"""
    try:
        # 获取用户数据
        users_data = _get_users_data()
        return render_template('users.html', users=users_data)
    except Exception as e:
        logger.error(f"渲染用户页面失败: {e}")
        return render_template('error.html', error=str(e)), 500

@user_bp.route('/api/users')
def api_users():
    """获取用户数据API"""
    try:
        users_data = _get_users_data()
        return jsonify({
            'success': True,
            'data': users_data
        })
    except Exception as e:
        logger.error(f"获取用户数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json() or request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器未初始化'}), 500
        
        # 验证用户
        user = user_manager.authenticate_user(username, password)
        if user:
            session['user_id'] = user.get('id') or user.get('user_id')
            session['username'] = user.get('username')
            session['role'] = user.get('role', 'user')
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'redirect': url_for('dashboard')
            })
        else:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
            
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/logout')
def logout():
    """用户登出"""
    try:
        # 清除会话
        session.clear()
        
        # 如果是AJAX请求，返回JSON
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True,
                'message': '已成功登出',
                'redirect': url_for('user.login')
            })
        
        # 否则重定向到登录页面
        return redirect(url_for('user.login'))
        
    except Exception as e:
        logger.error(f"用户登出失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/profile')
def profile():
    """用户个人资料页面"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('user.login'))
        
        if not user_manager:
            return render_template('error.html', error='用户管理器未初始化'), 500
        
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return render_template('error.html', error='用户不存在'), 404
        
        return render_template('profile.html', user=user)
        
    except Exception as e:
        logger.error(f"渲染用户资料页面失败: {e}")
        return render_template('error.html', error=str(e)), 500

def _get_users_data():
    """获取用户数据"""
    try:
        if not user_manager:
            return {
                'users': [],
                'stats': {
                    'total_users': 0,
                    'online_users': 0,
                    'active_users': 0,
                    'new_users_today': 0
                }
            }
        
        # 获取所有用户
        users = user_manager.get_all_users() or []
        
        # 计算统计数据
        total_users = len(users)
        online_users = 0  # 简化处理，实际需要会话管理
        active_users = len([u for u in users if u.get('status') == 'active'])
        
        # 今日新用户（简化计算）
        from datetime import datetime
        today = datetime.now().date()
        new_users_today = 0
        for user in users:
            if user.get('created_at'):
                try:
                    created_date = datetime.fromisoformat(user['created_at']).date()
                    if created_date == today:
                        new_users_today += 1
                except:
                    pass
        
        return {
            'users': users,
            'stats': {
                'total_users': total_users,
                'online_users': online_users,
                'active_users': active_users,
                'new_users_today': new_users_today
            }
        }
        
    except Exception as e:
        logger.error(f"获取用户数据失败: {e}")
        return {
            'users': [],
            'stats': {
                'total_users': 0,
                'online_users': 0,
                'active_users': 0,
                'new_users_today': 0
            }
        }