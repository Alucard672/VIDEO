#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复导入问题的脚本
将关键文件复制到正确的位置，并修复模块导入路径
"""

import os
import sys
import shutil
import re
from pathlib import Path
import importlib.util

def check_module_exists(module_name):
    """检查模块是否存在"""
    return importlib.util.find_spec(module_name) is not None

def fix_imports_in_file(file_path):
    """修复文件中的导入语句"""
    if not Path(file_path).exists():
        return
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # 修复导入语句中以数字开头的模块名
    # 例如: from content_fetch import xxx -> from content_fetch import xxx
    pattern = r'from\s+(\d+)_(\w+)(\s+import|\.)' 
    modified_content = re.sub(pattern, r'from \2\3', content)
    
    # 修复导入语句中的路径
    pattern = r'import\s+(\d+)_(\w+)(\s+as|\s*$|\s*,)'
    modified_content = re.sub(pattern, r'import \2\3', modified_content)
    
    # 修复模块别名导入
    pattern = r'from\s+module_\d+_(\w+)(\s+import|\.)' 
    modified_content = re.sub(pattern, r'from \1\2', modified_content)
    
    pattern = r'import\s+module_\d+_(\w+)(\s+as|\s*$|\s*,)'
    modified_content = re.sub(pattern, r'import \1\2', modified_content)
    
    if content != modified_content:
        with open(file_path, "w") as f:
            f.write(modified_content)
        print(f"已修复导入语句: {file_path}")

def main():
    """主函数"""
    print("开始修复导入问题...")
    
    # 获取当前目录
    current_dir = Path(__file__).parent.absolute()
    
    # 确保content_fetch目录存在
    content_fetch_dir = current_dir / "content_fetch"
    os.makedirs(content_fetch_dir, exist_ok=True)
    
    # 确保routes目录存在
    routes_dir = current_dir / "routes"
    os.makedirs(routes_dir, exist_ok=True)
    
    # 检查并创建__init__.py文件
    init_path = content_fetch_dir / "__init__.py"
    if not init_path.exists():
        with open(init_path, "w") as f:
            f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
内容采集模块
\"\"\"

from .fetch_news import NewsFetcher
from .fetch_videos import VideoFetcher

__all__ = ['NewsFetcher', 'VideoFetcher']
""")
        print(f"已创建 {init_path}")
    
    # 检查routes目录中的__init__.py
    routes_init_path = routes_dir / "__init__.py"
    if not routes_init_path.exists():
        with open(routes_init_path, "w") as f:
            f.write("# routes 包初始化文件\n")
        print(f"已创建 {routes_init_path}")
    
    # 修复web_app.py中的端口问题
    web_app_path = current_dir / "web_app.py"
    if web_app_path.exists():
        with open(web_app_path, "r") as f:
            content = f.read()
        
        # 检查是否包含端口5002
        if "port=5002" in content:
            content = content.replace("port=5002", "port=5001")
            with open(web_app_path, "w") as f:
                f.write(content)
            print("已将web_app.py中的端口从5002修改为5001")
    
    # 创建软链接或复制文件
    files_to_link = [
        ("api_content_simple.py", current_dir / "api_content_simple.py"),
        ("content_fetch_config.py", current_dir / "content_fetch_config.py"),
        ("database.py", current_dir / "database.py")
    ]
    
    for file_name, file_path in files_to_link:
        if file_path.exists():
            # 检查是否已经在sys.path中
            sys_path_file = Path(sys.path[0]) / file_name
            if not sys_path_file.exists():
                try:
                    # 尝试创建软链接
                    os.symlink(file_path, sys_path_file)
                    print(f"已创建软链接: {sys_path_file} -> {file_path}")
                except (OSError, PermissionError):
                    # 如果无法创建软链接，则复制文件
                    shutil.copy(file_path, sys_path_file)
                    print(f"已复制文件: {file_path} -> {sys_path_file}")
    
    # 修复所有Python文件中的导入语句
    for py_file in current_dir.glob("**/*.py"):
        # 跳过虚拟环境目录
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        fix_imports_in_file(py_file)
    
    # 创建一个简单的启动脚本
    start_script_path = current_dir / "start_fixed.py"
    with open(start_script_path, "w") as f:
        f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
修复后的启动脚本
\"\"\"

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# 导入必要的模块
try:
    from web_app import app
    
    if __name__ == "__main__":
        print("启动修复后的Web应用...")
        app.run(debug=True, host='0.0.0.0', port=5001)
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)
""")
    print(f"已创建启动脚本: {start_script_path}")
    
    print("导入问题修复完成")

if __name__ == "__main__":
    main()
