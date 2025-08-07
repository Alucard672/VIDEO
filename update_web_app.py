#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新Web应用，注册内容管理相关的API和页面
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def update_web_app():
    """更新web_app.py文件，添加内容管理功能"""
    
    web_app_path = project_root / "web_app.py"
    
    # 读取现有内容
    with open(web_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在导入部分添加内容扩展
    import_addition = """
# 导入内容管理扩展
try:
    from api_content_extensions import register_content_apis, register_content_pages
    content_extensions_available = True
except ImportError:
    content_extensions_available = False
    logger.warning("内容管理扩展模块未找到")
"""
    
    # 在主函数之前添加扩展注册
    extension_registration = """
# 注册内容管理扩展
if content_extensions_available:
    try:
        register_content_apis(app)
        register_content_pages(app)
        logger.info("内容管理扩展已注册")
    except Exception as e:
        logger.error(f"注册内容管理扩展失败: {e}")
"""
    
    # 查找合适的位置插入代码
    if "from api_content_extensions import" not in content:
        # 在导入部分添加
        import_pos = content.find("# 错误处理")
        if import_pos != -1:
            content = content[:import_pos] + import_addition + "\n" + content[import_pos:]
    
    if "register_content_apis(app)" not in content:
        # 在主函数之前添加
        main_pos = content.find('if __name__ == \'__main__\':')
        if main_pos != -1:
            content = content[:main_pos] + extension_registration + "\n" + content[main_pos:]
    
    # 写回文件
    with open(web_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Web应用更新完成")

if __name__ == "__main__":
    update_web_app()