#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 用于启动视频自动化管道系统
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        app.run(debug=True, host='0.0.0.0', port=5001)
    except ImportError as e:
        logger.error(f"导入失败: {e}")
        logger.error("请确保已安装所有依赖: pip install -r video-auto-pipeline/requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
