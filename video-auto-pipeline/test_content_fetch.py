#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容采集功能测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from database import init_database, get_db_connection
        print("✅ database 模块导入成功")
    except Exception as e:
        print(f"❌ database 模块导入失败: {e}")
        return False
    
    try:
        from content_fetch_config import ContentFetchConfig
        print("✅ content_fetch_config 模块导入成功")
    except Exception as e:
        print(f"❌ content_fetch_config 模块导入失败: {e}")
        return False
    
    try:
        from routes.content_fetch_routes import content_fetch_bp
        print("✅ content_fetch_routes 模块导入成功")
    except Exception as e:
        print(f"❌ content_fetch_routes 模块导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库功能"""
    print("🗄️  测试数据库功能...")
    
    try:
        from database import init_database, get_db_connection
        
        # 初始化数据库
        init_database()
        print("✅ 数据库初始化成功")
        
        # 测试连接
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ 数据库连接成功，共有 {len(tables)} 个表")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_content_fetch_config():
    """测试内容采集配置"""
    print("⚙️  测试内容采集配置...")
    
    try:
        from content_fetch_config import ContentFetchConfig
        
        config = ContentFetchConfig()
        sources = config.get_sources()
        categories = config.get_categories()
        
        print(f"✅ 配置加载成功，采集源: {len(sources)} 个，分类: {len(categories)} 个")
        return True
        
    except Exception as e:
        print(f"❌ 内容采集配置测试失败: {e}")
        return False

def test_web_app():
    """测试Web应用"""
    print("🌐 测试Web应用...")
    
    try:
        from web_app import app
        
        # 测试应用创建
        print("✅ Flask应用创建成功")
        
        # 测试路由注册
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))
        
        content_fetch_routes = [r for r in routes if 'content-fetch' in r]
        print(f"✅ 路由注册成功，内容采集相关路由: {len(content_fetch_routes)} 个")
        
        if content_fetch_routes:
            print("   内容采集路由:")
            for route in content_fetch_routes:
                print(f"   - {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web应用测试失败: {e}")
        return False

def start_test_server():
    """启动测试服务器"""
    print("🚀 启动测试服务器...")
    
    try:
        from web_app import app, socketio
        
        print("\n" + "="*60)
        print("🎉 测试服务器启动成功！")
        print("="*60)
        print("📱 访问地址: http://localhost:5002")
        print("🏠 主页: http://localhost:5002/")
        print("📥 内容采集: http://localhost:5002/content-fetch")
        print("="*60)
        print("🛑 按 Ctrl+C 停止服务器")
        print("="*60)
        
        # 启动服务器
        socketio.run(
            app,
            host='0.0.0.0',
            port=5002,
            debug=True,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动测试服务器失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 内容采集功能测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("数据库功能", test_database),
        ("内容采集配置", test_content_fetch_config),
        ("Web应用", test_web_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        
        choice = input("\n是否启动测试服务器？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            start_test_server()
    else:
        print("⚠️  部分测试失败，请检查相关功能。")
        
        choice = input("\n是否仍要启动测试服务器？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            start_test_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 测试中断，再见！")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")