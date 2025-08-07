#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模块重命名脚本
这个脚本将数字前缀的模块目录重命名为不带数字前缀的名称，并修复相关的导入关系
"""

import os
import sys
import re
import shutil
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('模块重命名')

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))

# 模块映射关系
MODULE_MAPPING = {
    "01_content_fetch": "content_fetch",
    "02_script_gen": "script_gen",
    "03_tts": "tts",
    "04_video_edit": "video_edit",
    "05_thumbnail": "thumbnail",
    "06_account_manager": "account_manager",
    "07_uploader": "uploader",
    "08_content_review": "content_review",
    "09_scheduler": "scheduler",
    "10_analytics": "analytics",
    "11_monitoring": "monitoring"
}

def rename_modules():
    """重命名模块目录"""
    logger.info("开始重命名模块目录...")
    
    for old_name, new_name in MODULE_MAPPING.items():
        old_path = PROJECT_ROOT / old_name
        new_path = PROJECT_ROOT / new_name
        
        if old_path.exists() and old_path.is_dir():
            if new_path.exists():
                logger.warning(f"目标目录已存在，无法重命名: {new_path}")
                continue
                
            try:
                # 重命名目录
                old_path.rename(new_path)
                logger.info(f"已重命名目录: {old_name} -> {new_name}")
            except Exception as e:
                logger.error(f"重命名目录失败: {old_name} -> {new_name}, 错误: {e}")
        else:
            logger.warning(f"源目录不存在: {old_path}")

def update_imports():
    """更新项目中的导入语句"""
    logger.info("开始更新导入语句...")
    
    # 创建正则表达式模式，用于匹配导入语句
    import_patterns = []
    for old_name, new_name in MODULE_MAPPING.items():
        # 匹配 from content_fetch import ...
        import_patterns.append((
            re.compile(rf"from\s+{old_name}(\s+import|\.)"),
            f"from {new_name}\\1"
        ))
        # 匹配 import 01_content_fetch
        import_patterns.append((
            re.compile(rf"import\s+{old_name}(\s+as|\s*$|\s*,)"),
            f"import {new_name}\\1"
        ))
    
    # 遍历所有Python文件
    for py_file in PROJECT_ROOT.glob("**/*.py"):
        # 跳过虚拟环境目录
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
            
        try:
            # 读取文件内容
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 应用所有替换模式
            modified = False
            for pattern, replacement in import_patterns:
                new_content = pattern.sub(replacement, content)
                if new_content != content:
                    content = new_content
                    modified = True
            
            # 如果文件被修改，写回文件
            if modified:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已更新导入语句: {py_file}")
        except Exception as e:
            logger.error(f"处理文件失败: {py_file}, 错误: {e}")

def update_init_file():
    """更新主__init__.py文件"""
    logger.info("更新主__init__.py文件...")
    
    init_file = PROJECT_ROOT / "__init__.py"
    if not init_file.exists():
        logger.warning(f"主__init__.py文件不存在: {init_file}")
        return
    
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
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

# 导出所有模块
__all__ = [
    "content_fetch",
    "script_gen",
    "tts",
    "video_edit",
    "thumbnail",
    "account_manager",
    "uploader",
    "content_review",
    "scheduler",
    "analytics",
    "monitoring"
]

# 导入所有模块
try:
    import content_fetch
    import script_gen
    import tts
    import video_edit
    import thumbnail
    import account_manager
    import uploader
    import content_review
    import scheduler
    import analytics
    import monitoring
except ImportError as e:
    print(f"导入模块失败: {e}")
""")
        logger.info(f"已更新主__init__.py文件")
    except Exception as e:
        logger.error(f"更新主__init__.py文件失败: {e}")

def main():
    """主函数"""
    logger.info("开始重命名模块并修复导入关系...")
    
    # 重命名模块目录
    rename_modules()
    
    # 更新导入语句
    update_imports()
    
    # 更新主__init__.py文件
    update_init_file()
    
    logger.info("模块重命名和导入修复完成！")
    logger.info("请重启应用以应用更改")

if __name__ == "__main__":
    main()