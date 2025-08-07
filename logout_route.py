#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退出登录路由
"""

from flask import session, flash, redirect, url_for

def add_logout_route(app):
    """添加退出登录路由到Flask应用"""
    
    @app.route('/logout')
    def logout():
        """退出登录"""
        try:
            # 清除会话
            session.clear()
            flash('您已成功退出登录', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'退出登录时发生错误: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
    
    return app