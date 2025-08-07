from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from user_manager import UserManager
import logging

logger = logging.getLogger(__name__)

# 创建账号管理蓝图
account_bp = Blueprint('account', __name__)

# 初始化用户管理器
try:
    user_manager = UserManager()
except Exception as e:
    logger.error(f"初始化用户管理器失败: {e}")
    user_manager = None

@account_bp.route('/accounts')
def accounts():
    """账号管理页面"""
    try:
        # 获取账号数据
        accounts_data = _get_accounts_data()
        return render_template('accounts.html', accounts=accounts_data)
    except Exception as e:
        logger.error(f"渲染账号页面失败: {e}")
        return render_template('error.html', error=str(e)), 500

@account_bp.route('/api/accounts')
def api_accounts():
    """获取账号数据API"""
    try:
        accounts_data = _get_accounts_data()
        return jsonify({
            'success': True,
            'data': accounts_data
        })
    except Exception as e:
        logger.error(f"获取账号数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@account_bp.route('/api/accounts/<account_id>', methods=['GET'])
def api_get_account(account_id):
    """获取单个账号信息"""
    try:
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器未初始化'}), 500
            
        account = user_manager.get_user_by_id(account_id)
        if not account:
            return jsonify({'success': False, 'error': '账号不存在'}), 404
            
        return jsonify({
            'success': True,
            'data': account
        })
    except Exception as e:
        logger.error(f"获取账号信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@account_bp.route('/api/accounts', methods=['POST'])
def api_create_account():
    """创建新账号"""
    try:
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器未初始化'}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
            
        # 验证必需字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400
        
        # 创建账号
        result = user_manager.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'user')
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': '账号创建成功',
                'data': result
            })
        else:
            return jsonify({'success': False, 'error': '账号创建失败'}), 500
            
    except Exception as e:
        logger.error(f"创建账号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@account_bp.route('/api/accounts/<account_id>', methods=['PUT'])
def api_update_account(account_id):
    """更新账号信息"""
    try:
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器未初始化'}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
            
        # 更新账号
        result = user_manager.update_user(account_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'message': '账号更新成功'
            })
        else:
            return jsonify({'success': False, 'error': '账号更新失败'}), 500
            
    except Exception as e:
        logger.error(f"更新账号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@account_bp.route('/api/accounts/<account_id>', methods=['DELETE'])
def api_delete_account(account_id):
    """删除账号"""
    try:
        if not user_manager:
            return jsonify({'success': False, 'error': '用户管理器未初始化'}), 500
            
        result = user_manager.delete_user(account_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': '账号删除成功'
            })
        else:
            return jsonify({'success': False, 'error': '账号删除失败'}), 500
            
    except Exception as e:
        logger.error(f"删除账号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_accounts_data():
    """获取账号数据"""
    try:
        if not user_manager:
            return {
                'users': [],
                'stats': {
                    'total_users': 0,
                    'active_users': 0,
                    'admin_users': 0,
                    'new_users_today': 0
                }
            }
        
        # 获取所有用户
        users = user_manager.get_all_users() or []
        
        # 计算统计数据
        total_users = len(users)
        active_users = len([u for u in users if u.get('status') == 'active'])
        admin_users = len([u for u in users if u.get('role') == 'admin'])
        
        # 今日新用户（简化计算）
        from datetime import datetime, timedelta
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
                'active_users': active_users,
                'admin_users': admin_users,
                'new_users_today': new_users_today
            }
        }
        
    except Exception as e:
        logger.error(f"获取账号数据失败: {e}")
        return {
            'users': [],
            'stats': {
                'total_users': 0,
                'active_users': 0,
                'admin_users': 0,
                'new_users_today': 0
            }
        }