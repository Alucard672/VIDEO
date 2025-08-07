#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目清理和重组脚本 v2.0
这个脚本将帮助清理和重组项目结构，解决以下问题：
1. 嵌套目录结构
2. 重复文件
3. 模块命名问题
4. 导入路径问题
5. 冗余配置和页面
"""

import os
import sys
import shutil
import re
import sqlite3
from pathlib import Path
import logging
import json
import filecmp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('项目清理')

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = PROJECT_ROOT.parent

# 定义需要保留的文件
KEEP_FILES = {
    'web_app.py': True,           # 主Web应用
    'web_app_complete.py': False, # 完整版Web应用（备份）
    'web_app_old.py': False,      # 旧版Web应用（备份）
    'web_app_backup.py': False,   # 备份Web应用
    'web_app_broken.py': False,   # 损坏的Web应用
    'start.py': True,             # 原始启动脚本
    'start_fixed.py': True,       # 修复后的启动脚本
    'fix_imports.py': True,       # 导入修复脚本
    'cleanup_project.py': True,   # 项目清理脚本
}

# 定义数据库修复SQL
DB_FIX_SQL = [
    """
    -- 检查并添加task_name列
    SELECT COUNT(*) FROM pragma_table_info('tasks') WHERE name='task_name';
    """,
    """
    -- 如果task_name列不存在，添加它
    ALTER TABLE tasks ADD COLUMN task_name TEXT DEFAULT '未命名任务';
    """,
    """
    -- 检查并添加last_login列
    SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='last_login';
    """,
    """
    -- 如果last_login列不存在，添加它
    ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    """
]

def check_nested_directory():
    """检查是否存在嵌套的video-auto-pipeline目录"""
    nested_dir = PROJECT_ROOT / "video-auto-pipeline"
    if nested_dir.exists() and nested_dir.is_dir():
        logger.info(f"发现嵌套目录: {nested_dir}")
        return nested_dir
    
    # 检查备份目录
    backup_dir = PROJECT_ROOT / "video-auto-pipeline_backup"
    if backup_dir.exists() and backup_dir.is_dir():
        logger.info(f"发现备份目录: {backup_dir}")
        return backup_dir
    
    return None

def merge_nested_directory(nested_dir):
    """合并嵌套目录中的文件到主目录"""
    logger.info(f"开始合并嵌套目录: {nested_dir}")
    
    # 列出嵌套目录中的所有文件和目录
    for item in nested_dir.iterdir():
        target_path = PROJECT_ROOT / item.name
        
        # 如果目标路径已存在
        if target_path.exists():
            if target_path.is_dir():
                logger.info(f"目录已存在，合并内容: {item.name}")
                # 递归合并目录内容
                for sub_item in item.iterdir():
                    sub_target = target_path / sub_item.name
                    if not sub_target.exists():
                        if sub_item.is_dir():
                            shutil.copytree(sub_item, sub_target)
                            logger.info(f"  复制目录: {sub_item.name} -> {sub_target}")
                        else:
                            shutil.copy2(sub_item, sub_target)
                            logger.info(f"  复制文件: {sub_item.name} -> {sub_target}")
            else:
                # 如果是文件，检查是否相同
                try:
                    if filecmp.cmp(item, target_path, shallow=False):
                        logger.info(f"文件相同，跳过: {item.name}")
                    else:
                        backup_path = target_path.with_name(f"{target_path.stem}_backup{target_path.suffix}")
                        shutil.copy2(target_path, backup_path)
                        logger.info(f"文件不同，备份原文件: {target_path} -> {backup_path}")
                        shutil.copy2(item, target_path)
                        logger.info(f"更新文件: {item} -> {target_path}")
                except Exception as e:
                    logger.error(f"比较文件失败: {e}")
        else:
            # 如果目标路径不存在，直接复制
            if item.is_dir():
                shutil.copytree(item, target_path)
                logger.info(f"复制目录: {item.name} -> {target_path}")
            else:
                shutil.copy2(item, target_path)
                logger.info(f"复制文件: {item.name} -> {target_path}")
    
    # 重命名嵌套目录
    backup_dir = nested_dir.with_name("video-auto-pipeline_backup")
    if nested_dir.name != "video-auto-pipeline_backup":
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        nested_dir.rename(backup_dir)
        logger.info(f"嵌套目录已重命名为备份: {nested_dir} -> {backup_dir}")

def fix_module_names():
    """修复以数字开头的模块名"""
    logger.info("开始修复模块名...")
    
    # 查找所有以数字开头的目录
    number_pattern = re.compile(r'^(\d+)_(.+)$')
    module_dirs = []
    
    # 收集所有模块目录
    for item in PROJECT_ROOT.iterdir():
        if item.is_dir():
            match = number_pattern.match(item.name)
            if match:
                module_dirs.append(item)
    
    # 创建或更新主__init__.py文件，导入所有模块
    main_init_file = PROJECT_ROOT / "__init__.py"
    with open(main_init_file, 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
视频自动化流水线项目
这个文件自动导入所有模块，使它们可以通过标准Python导入语法访问
\"\"\"

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

""")
        
        # 为每个模块添加导入语句
        for module_dir in module_dirs:
            module_name = module_dir.name
            f.write(f"""
# 导入 {module_name} 模块
try:
    from . import {module_name}
    print(f"成功导入模块: {module_name}")
except ImportError as e:
    print(f"导入模块失败: {module_name} - {{e}}")
""")
    
    logger.info(f"已创建主初始化文件: {main_init_file}")
    
    # 确保每个模块目录都有__init__.py文件
    for module_dir in module_dirs:
        init_file = module_dir / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
{module_dir.name} 模块
\"\"\"

# 导入模块中的所有Python文件
import os
from pathlib import Path

# 自动导入当前目录中的所有Python模块
__all__ = []
for py_file in Path(__file__).parent.glob("*.py"):
    if py_file.name != "__init__.py":
        module_name = py_file.stem
        __all__.append(module_name)
        exec(f"from .{{module_name}} import *")
""")
            logger.info(f"已创建模块初始化文件: {init_file}")

def cleanup_duplicate_files():
    """清理重复的文件"""
    logger.info("开始清理重复文件...")
    
    # 查找所有web_app相关文件
    web_app_files = []
    for item in PROJECT_ROOT.glob("web_app*.py"):
        if item.is_file():
            web_app_files.append(item)
    
    logger.info(f"找到{len(web_app_files)}个web_app相关文件")
    
    # 整理文件
    for file in web_app_files:
        if file.name in KEEP_FILES:
            if KEEP_FILES[file.name]:
                logger.info(f"保留文件: {file.name}")
            else:
                backup_dir = PROJECT_ROOT / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / file.name
                shutil.copy2(file, backup_path)
                logger.info(f"备份文件: {file.name} -> backups/{file.name}")
        else:
            logger.info(f"未知文件: {file.name}，保留")

def fix_database():
    """修复数据库结构"""
    logger.info("开始修复数据库结构...")
    
    db_path = PROJECT_ROOT / "tasks.db"
    if not db_path.exists():
        logger.warning(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行修复SQL
        for sql in DB_FIX_SQL:
            try:
                result = cursor.execute(sql).fetchone()
                if result and result[0] == 0:
                    # 列不存在，需要添加
                    next_sql = DB_FIX_SQL[DB_FIX_SQL.index(sql) + 1]
                    cursor.execute(next_sql)
                    conn.commit()
                    logger.info(f"执行SQL: {next_sql}")
            except sqlite3.Error as e:
                logger.error(f"执行SQL失败: {e}")
        
        conn.close()
        logger.info("数据库修复完成")
    except sqlite3.Error as e:
        logger.error(f"连接数据库失败: {e}")

def create_fixed_start_script():
    """创建修复后的启动脚本"""
    logger.info("创建修复后的启动脚本...")
    
    script_path = PROJECT_ROOT / "start_fixed.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
修复后的启动脚本
这个脚本将正确设置Python路径，修复数据库结构，并启动Web应用
\"\"\"

import os
import sys
import socket
import sqlite3
from pathlib import Path
import importlib.util
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('启动脚本')

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 打印Python路径
logger.info("Python路径:")
for path in sys.path:
    logger.info(f"  - {path}")

# 修复数据库结构
def fix_database():
    \"\"\"修复数据库结构\"\"\"
    logger.info("检查并修复数据库结构...")
    
    db_path = current_dir / "tasks.db"
    if not db_path.exists():
        logger.warning(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查并添加task_name列
        try:
            result = cursor.execute("SELECT COUNT(*) FROM pragma_table_info('tasks') WHERE name='task_name'").fetchone()
            if result and result[0] == 0:
                cursor.execute("ALTER TABLE tasks ADD COLUMN task_name TEXT DEFAULT '未命名任务'")
                conn.commit()
                logger.info("已添加task_name列到tasks表")
        except sqlite3.Error as e:
            logger.error(f"修复tasks表失败: {e}")
        
        # 检查并添加last_login列
        try:
            result = cursor.execute("SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='last_login'").fetchone()
            if result and result[0] == 0:
                cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
                logger.info("已添加last_login列到users表")
        except sqlite3.Error as e:
            logger.error(f"修复users表失败: {e}")
        
        conn.close()
        logger.info("数据库检查完成")
    except sqlite3.Error as e:
        logger.error(f"连接数据库失败: {e}")

# 执行数据库修复
fix_database()

# 检查模块可用性
modules_to_check = [
    'api_content_simple', 
    'content_fetch_config', 
    'database', 
    'task_manager', 
    'user_manager'
]

logger.info("\\n模块可用性检查:")
for module_name in modules_to_check:
    try:
        module = importlib.import_module(module_name)
        logger.info(f"  ✓ {module_name} 可用")
    except ImportError as e:
        logger.info(f"  ✗ {module_name} 不可用: {e}")

# 查找可用端口
def find_available_port(start_port=5000, max_attempts=10):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port  # 如果没有找到可用端口，返回起始端口

# 导入web_app模块
try:
    import web_app
    logger.info("成功导入web_app.app")
    
    # 查找可用端口
    port = find_available_port(5000)
    logger.info(f"启动修复后的Web应用，端口: {port}...")
    
    # 启动Web应用
    web_app.app.run(host='127.0.0.1', port=port, debug=True)
except ImportError as e:
    logger.error(f"导入web_app失败: {e}")
    
    # 尝试导入web_app_complete
    try:
        import web_app_complete
        logger.info("成功导入web_app_complete")
        
        # 查找可用端口
        port = find_available_port(5000)
        logger.info(f"启动完整版Web应用，端口: {port}...")
        
        # 启动Web应用
        web_app_complete.app.run(host='127.0.0.1', port=port, debug=True)
    except ImportError as e:
        logger.error(f"导入web_app_complete失败: {e}")
        logger.error("无法启动Web应用，请检查项目结构和依赖")
""")
    logger.info(f"已创建启动脚本: {script_path}")

def main():
    """主函数"""
    logger.info("开始清理和重组项目...")
    
    # 检查并合并嵌套目录
    nested_dir = check_nested_directory()
    if nested_dir:
        merge_nested_directory(nested_dir)
    
    # 修复模块名
    fix_module_names()
    
    # 清理重复文件
    cleanup_duplicate_files()
    
    # 修复数据库
    fix_database()
    
    # 创建修复后的启动脚本
    create_fixed_start_script()
    
    logger.info("项目清理和重组完成！")
    logger.info("请运行 python start_fixed.py 启动应用")

if __name__ == "__main__":
    main()