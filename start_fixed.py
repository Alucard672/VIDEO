#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 用于启动视频自动化管道系统
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 创建日志目录
os.makedirs('video-auto-pipeline/logs', exist_ok=True)

# 配置日志
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                 datefmt='%Y-%m-%d %H:%M:%S')

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# 文件处理器 - 使用当前日期作为文件名
log_file = f'video-auto-pipeline/logs/app_{datetime.now().strftime("%Y%m%d")}.log'
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info(f"日志文件: {os.path.abspath(log_file)}")

def main():
    try:
        # 将工作目录切换到video-auto-pipeline
        os.chdir('video-auto-pipeline')
        logger.info("已切换到video-auto-pipeline目录")
        
        # 添加当前目录到Python路径
        sys.path.insert(0, os.getcwd())
        
        # 初始化数据库
        logger.info("正在初始化数据库...")
        from database import init_db
        init_db()
        logger.info("数据库初始化完成")
        
        # 导入并运行web应用
        logger.info("正在启动Web应用...")
        from web_app import app
        
        # 确保web_app也使用我们的日志配置
        app_logger = logging.getLogger('web_app')
        app_logger.info("Web应用日志系统已初始化")
        
        app.run(debug=True, host='0.0.0.0', port=5002)
    except ImportError as e:
        logger.error(f"导入失败: {e}")
        logger.error("请确保已安装所有依赖: pip install -r video-auto-pipeline/requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
