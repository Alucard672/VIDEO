#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频搬运矩阵自动化系统 - 主程序
"""

import argparse
import sys
from pathlib import Path
from loguru import logger
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config import LogConfig, LOGS_DIR

# 配置日志
logger.add(
    LogConfig.LOG_FILE,
    level=LogConfig.LOG_LEVEL,
    format=LogConfig.LOG_FORMAT,
    rotation="1 day",
    retention="7 days"
)

def setup_environment():
    """设置运行环境"""
    logger.info("正在设置运行环境...")
    
    # 创建必要的目录
    from config import DATA_DIR, VIDEOS_DIR, AUDIO_DIR, THUMBNAILS_DIR, LOGS_DIR
    
    for dir_path in [DATA_DIR, VIDEOS_DIR, AUDIO_DIR, THUMBNAILS_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {dir_path}")
    
    logger.info("环境设置完成")

def run_content_fetch():
    """运行内容采集模块"""
    logger.info("开始内容采集...")
    try:
        # 这里将导入并运行内容采集模块
        # from content_fetch.fetch_news import fetch_news
        # from content_fetch.fetch_videos import fetch_videos
        logger.info("内容采集完成")
        return True
    except Exception as e:
        logger.error(f"内容采集失败: {e}")
        return False

def run_script_generation():
    """运行脚本生成模块"""
    logger.info("开始脚本生成...")
    try:
        # 这里将导入并运行脚本生成模块
        # from script_gen.generate_script import generate_script
        logger.info("脚本生成完成")
        return True
    except Exception as e:
        logger.error(f"脚本生成失败: {e}")
        return False

def run_tts_generation():
    """运行AI配音模块"""
    logger.info("开始AI配音生成...")
    try:
        # 这里将导入并运行TTS模块
        # from tts.tts_generate import generate_tts
        logger.info("AI配音生成完成")
        return True
    except Exception as e:
        logger.error(f"AI配音生成失败: {e}")
        return False

def run_video_editing():
    """运行视频剪辑模块"""
    logger.info("开始视频剪辑...")
    try:
        # 这里将导入并运行视频剪辑模块
        # from video_edit.edit_merge import edit_video
        logger.info("视频剪辑完成")
        return True
    except Exception as e:
        logger.error(f"视频剪辑失败: {e}")
        return False

def run_thumbnail_generation():
    """运行封面生成模块"""
    logger.info("开始封面生成...")
    try:
        # 这里将导入并运行封面生成模块
        # from thumbnail.thumbnail_gen import generate_thumbnail
        logger.info("封面生成完成")
        return True
    except Exception as e:
        logger.error(f"封面生成失败: {e}")
        return False

def run_content_review():
    """运行内容审核模块"""
    logger.info("开始内容审核...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("content_review", "08_content_review/content_review.py")
        content_review = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(content_review)
        ContentReviewer = content_review.ContentReviewer
        
        reviewer = ContentReviewer()
        
        # 模拟审核内容
        test_content = {
            "title": "测试视频标题",
            "description": "这是一个测试视频描述",
            "tags": ["测试", "视频"]
        }
        
        result = reviewer.review_video_content(test_content)
        logger.info(f"内容审核完成，通过: {result['passed']}")
        return True
    except Exception as e:
        logger.error(f"内容审核失败: {e}")
        return False

def run_upload():
    """运行自动上传模块"""
    logger.info("开始自动上传...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("scheduler", "09_scheduler/scheduler.py")
        scheduler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scheduler)
        PublishScheduler = scheduler.PublishScheduler
        
        scheduler_instance = PublishScheduler()
        
        # 模拟调度上传任务
        video_info = {
            "video_path": "test_video.mp4",
            "title": "测试视频标题",
            "description": "这是一个测试视频",
            "tags": ["测试", "视频"]
        }
        
        result = scheduler_instance.schedule_video_publish(video_info, "douyin", 1)
        logger.info(f"发布调度完成，任务ID: {result['task_id']}")
        return True
    except Exception as e:
        logger.error(f"自动上传失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频搬运矩阵自动化系统")
    parser.add_argument("--modules", nargs="+", 
                       choices=["fetch", "script", "tts", "edit", "thumbnail", "review", "upload"],
                       help="指定要运行的模块")
    parser.add_argument("--all", action="store_true", help="运行所有模块")
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("视频搬运矩阵自动化系统启动")
    logger.info("=" * 50)
    
    # 设置环境
    setup_environment()
    
    # 定义模块执行顺序
    modules = [
        ("fetch", run_content_fetch, "内容采集"),
        ("script", run_script_generation, "脚本生成"),
        ("tts", run_tts_generation, "AI配音"),
        ("edit", run_video_editing, "视频剪辑"),
        ("thumbnail", run_thumbnail_generation, "封面生成"),
        ("review", run_content_review, "内容审核"),
        ("upload", run_upload, "自动上传")
    ]
    
    # 确定要运行的模块
    if args.all:
        modules_to_run = [name for name, _, _ in modules]
    elif args.modules:
        modules_to_run = args.modules
    else:
        # 默认运行所有模块
        modules_to_run = [name for name, _, _ in modules]
    
    # 执行模块
    success_count = 0
    total_count = len(modules_to_run)
    
    for module_name, module_func, module_desc in modules:
        if module_name in modules_to_run:
            logger.info(f"开始执行模块: {module_desc}")
            start_time = time.time()
            
            if module_func():
                success_count += 1
                elapsed_time = time.time() - start_time
                logger.info(f"模块 {module_desc} 执行成功，耗时: {elapsed_time:.2f}秒")
            else:
                elapsed_time = time.time() - start_time
                logger.error(f"模块 {module_desc} 执行失败，耗时: {elapsed_time:.2f}秒")
    
    # 输出执行结果
    logger.info("=" * 50)
    logger.info(f"执行完成！成功: {success_count}/{total_count}")
    logger.info("=" * 50)
    
    if success_count == total_count:
        logger.info("🎉 所有模块执行成功！")
        return 0
    else:
        logger.error("❌ 部分模块执行失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 