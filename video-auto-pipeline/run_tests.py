#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试运行脚本
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_system_tests():
    """运行系统测试"""
    print("🚀 启动系统测试...")
    
    try:
        # 运行测试脚本
        result = subprocess.run([
            sys.executable, 'test_system.py'
        ], cwd=project_root, capture_output=True, text=True)
        
        print("测试输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False

def start_web_server():
    """启动Web服务器"""
    print("🌐 启动Web服务器...")
    
    try:
        # 启动web应用
        process = subprocess.Popen([
            sys.executable, 'web_app.py'
        ], cwd=project_root)
        
        print("✅ Web服务器已启动")
        print("📱 访问地址: http://localhost:5002")
        print("🔧 内容采集管理: http://localhost:5002/content-fetch")
        print("⏹️  按 Ctrl+C 停止服务器")
        
        # 等待用户中断
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 正在停止Web服务器...")
            process.terminate()
            process.wait()
            print("✅ Web服务器已停止")
        
        return True
        
    except Exception as e:
        print(f"❌ 启动Web服务器失败: {e}")
        return False

def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("🎯 视频自动化处理系统 - 测试与启动工具")
    print("="*60)
    print("1. 运行系统测试")
    print("2. 启动Web服务器")
    print("3. 运行测试并启动服务器")
    print("4. 查看系统状态")
    print("0. 退出")
    print("="*60)

def check_system_status():
    """检查系统状态"""
    print("🔍 检查系统状态...")
    
    # 检查必要文件
    required_files = [
        'web_app.py',
        'database.py',
        'content_fetch_config.py',
        'enhanced_fetcher.py',
        'routes/content_fetch_routes.py',
        'templates/content_fetch.html'
    ]
    
    print("\n📁 文件检查:")
    all_files_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (缺失)")
            all_files_exist = False
    
    # 检查数据目录
    data_dir = project_root / 'data'
    if data_dir.exists():
        print(f"  ✅ data/ 目录存在")
        db_file = data_dir / 'video_pipeline.db'
        if db_file.exists():
            print(f"  ✅ 数据库文件存在 ({db_file.stat().st_size} 字节)")
        else:
            print(f"  ⚠️  数据库文件不存在，将在首次运行时创建")
    else:
        print(f"  ⚠️  data/ 目录不存在，将在首次运行时创建")
    
    # 检查模板文件
    templates_dir = project_root / 'templates'
    if templates_dir.exists():
        template_count = len(list(templates_dir.glob('*.html')))
        print(f"  ✅ templates/ 目录存在 ({template_count} 个模板文件)")
    else:
        print(f"  ❌ templates/ 目录不存在")
        all_files_exist = False
    
    # 检查路由文件
    routes_dir = project_root / 'routes'
    if routes_dir.exists():
        route_count = len(list(routes_dir.glob('*.py')))
        print(f"  ✅ routes/ 目录存在 ({route_count} 个路由文件)")
    else:
        print(f"  ❌ routes/ 目录不存在")
        all_files_exist = False
    
    print(f"\n📊 系统状态: {'✅ 就绪' if all_files_exist else '❌ 不完整'}")
    
    return all_files_exist

def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("请选择操作 (0-4): ").strip()
            
            if choice == "1":
                print("\n" + "="*60)
                run_system_tests()
                input("\n按回车键继续...")
                
            elif choice == "2":
                print("\n" + "="*60)
                start_web_server()
                input("\n按回车键继续...")
                
            elif choice == "3":
                print("\n" + "="*60)
                print("🔄 运行测试并启动服务器...")
                if run_system_tests():
                    print("\n✅ 测试通过，启动Web服务器...")
                    time.sleep(2)
                    start_web_server()
                else:
                    print("\n❌ 测试失败，请检查系统配置")
                input("\n按回车键继续...")
                
            elif choice == "4":
                print("\n" + "="*60)
                check_system_status()
                input("\n按回车键继续...")
                
            elif choice == "0":
                print("\n👋 再见！")
                break
                
            else:
                print("\n❌ 无效选择，请重新输入")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 操作失败: {e}")
            input("按回车键继续...")

if __name__ == "__main__":
    main()