#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统功能测试脚本
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_database():
    """测试数据库功能"""
    print("🔍 测试数据库功能...")
    
    try:
        from database import init_database, get_db_connection, get_database_stats
        
        # 初始化数据库
        init_database()
        
        # 测试连接
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        # 获取统计信息
        stats = get_database_stats()
        
        print(f"✅ 数据库连接正常，用户数量: {user_count}")
        print(f"✅ 数据库统计: {stats}")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_content_fetch_config():
    """测试内容采集配置"""
    print("🔍 测试内容采集配置...")
    
    try:
        from content_fetch_config import ContentFetchConfig
        
        config = ContentFetchConfig()
        
        # 测试获取采集源
        sources = config.get_sources()
        print(f"✅ 采集源数量: {len(sources)}")
        
        # 测试获取分类
        categories = config.get_categories()
        print(f"✅ 分类数量: {len(categories)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 内容采集配置测试失败: {e}")
        return False

def test_enhanced_fetcher():
    """测试增强采集器"""
    print("🔍 测试增强采集器...")
    
    try:
        from enhanced_fetcher import EnhancedContentFetcher
        
        fetcher = EnhancedContentFetcher()
        
        # 测试采集器初始化
        print("✅ 增强采集器初始化成功")
        
        # 测试简单的网页采集
        test_source = {
            'id': 999,
            'name': '测试源',
            'platform': 'test',
            'url': 'https://httpbin.org/json',
            'category': 'test',
            'fetch_limit': 1
        }
        
        results = fetcher.fetch_from_source(test_source, limit=1)
        print(f"✅ 测试采集成功，结果数量: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强采集器测试失败: {e}")
        return False

def test_web_server():
    """测试Web服务器"""
    print("🔍 测试Web服务器连接...")
    
    try:
        # 测试本地服务器连接
        response = requests.get('http://localhost:5002', timeout=5)
        if response.status_code == 200:
            print("✅ Web服务器连接正常")
            return True
        else:
            print(f"⚠️  Web服务器响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Web服务器未启动或无法连接")
        return False
    except Exception as e:
        print(f"❌ Web服务器测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("🔍 测试文件结构...")
    
    required_files = [
        'web_app.py',
        'database.py',
        'content_fetch_config.py',
        'routes/content_fetch_routes.py',
        'templates/content_fetch.html',
        'templates/base.html'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    modules_to_test = [
        'database',
        'content_fetch_config',
        'routes.content_fetch_routes'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
        except ImportError as e:
            print(f"❌ {module} 导入失败: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始系统功能测试")
    print("=" * 60)
    
    tests = [
        ("文件结构", test_file_structure),
        ("模块导入", test_imports),
        ("数据库功能", test_database),
        ("内容采集配置", test_content_fetch_config),
        ("增强采集器", test_enhanced_fetcher),
        ("Web服务器", test_web_server)
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
        print("🎉 所有测试通过！系统准备就绪。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能。")
        return False

def show_system_info():
    """显示系统信息"""
    print("\n" + "=" * 60)
    print("📋 系统信息:")
    print("=" * 60)
    
    print(f"Python版本: {sys.version}")
    print(f"项目路径: {project_root}")
    print(f"数据库路径: {project_root / 'data' / 'video_pipeline.db'}")
    print(f"Web服务地址: http://localhost:5002")
    print(f"内容采集页面: http://localhost:5002/content-fetch")
    
    # 显示目录结构
    print(f"\n📁 项目结构:")
    important_paths = [
        'templates/',
        'routes/',
        'data/',
        'static/',
        'logs/'
    ]
    
    for path in important_paths:
        full_path = project_root / path
        if full_path.exists():
            if full_path.is_dir():
                file_count = len(list(full_path.glob('*')))
                print(f"  {path} ({file_count} 个文件)")
            else:
                print(f"  {path}")
        else:
            print(f"  {path} (不存在)")

if __name__ == "__main__":
    show_system_info()
    
    print("\n" + "=" * 60)
    print("选择操作:")
    print("1. 运行完整测试")
    print("2. 仅测试数据库")
    print("3. 仅测试采集功能")
    print("4. 仅测试Web服务器")
    print("0. 退出")
    print("=" * 60)
    
    try:
        choice = input("请输入选择 (0-4): ").strip()
        
        if choice == "1":
            run_all_tests()
        elif choice == "2":
            test_database()
        elif choice == "3":
            test_content_fetch_config()
            test_enhanced_fetcher()
        elif choice == "4":
            test_web_server()
        elif choice == "0":
            print("👋 再见！")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 测试中断，再见！")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")