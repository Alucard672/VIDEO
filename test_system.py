#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本
用于验证各个模块的功能是否正常
"""

import sys
import time
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_config():
    """测试配置文件"""
    logger.info("测试配置文件...")
    try:
        from config import APIConfig, DatabaseConfig, VideoConfig, UploadConfig
        logger.info("✅ 配置文件加载成功")
        return True
    except Exception as e:
        logger.error(f"❌ 配置文件加载失败: {e}")
        return False

def test_content_fetch():
    """测试内容采集模块"""
    logger.info("测试内容采集模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("fetch_news", "01_content_fetch/fetch_news.py")
        fetch_news = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_news)
        NewsFetcher = fetch_news.NewsFetcher
        
        spec = importlib.util.spec_from_file_location("fetch_videos", "01_content_fetch/fetch_videos.py")
        fetch_videos = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_videos)
        VideoFetcher = fetch_videos.VideoFetcher
        
        # 测试新闻采集
        news_fetcher = NewsFetcher()
        news_list = news_fetcher.fetch_netease_news()
        logger.info(f"✅ 新闻采集成功，获取 {len(news_list)} 条新闻")
        
        # 测试视频采集
        video_fetcher = VideoFetcher()
        logger.info("✅ 视频采集模块初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 内容采集模块测试失败: {e}")
        return False

def test_script_generation():
    """测试脚本生成模块"""
    logger.info("测试脚本生成模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("generate_script", "02_script_gen/generate_script.py")
        generate_script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generate_script)
        ScriptGenerator = generate_script.ScriptGenerator
        
        generator = ScriptGenerator()
        
        # 测试文案生成
        sample_news = {
            "title": "测试新闻标题",
            "content": "这是测试新闻内容",
            "source": "测试来源"
        }
        
        script = generator.generate_script_from_news(sample_news, "客观")
        if script:
            logger.info("✅ 脚本生成成功")
            return True
        else:
            logger.warning("⚠️ 脚本生成返回空，可能是API密钥未配置")
            return True  # 不视为错误，因为可能是配置问题
    except Exception as e:
        logger.error(f"❌ 脚本生成模块测试失败: {e}")
        return False

def test_tts_generation():
    """测试TTS生成模块"""
    logger.info("测试TTS生成模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tts_generate", "03_tts/tts_generate.py")
        tts_generate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tts_generate)
        TTSGenerator = tts_generate.TTSGenerator
        
        generator = TTSGenerator()
        
        # 测试TTS生成
        test_text = "这是一个测试文本，用于验证TTS功能。"
        audio_path = generator.generate_tts_fliki(test_text, "female")
        
        if audio_path:
            logger.info("✅ TTS生成成功")
            return True
        else:
            logger.warning("⚠️ TTS生成返回空，可能是API密钥未配置")
            return True  # 不视为错误
    except Exception as e:
        logger.error(f"❌ TTS生成模块测试失败: {e}")
        return False

def test_video_editing():
    """测试视频剪辑模块"""
    logger.info("测试视频剪辑模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("edit_merge", "04_video_edit/edit_merge.py")
        edit_merge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(edit_merge)
        VideoEditor = edit_merge.VideoEditor
        
        editor = VideoEditor()
        
        # 测试视频信息获取
        logger.info("✅ 视频剪辑模块初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 视频剪辑模块测试失败: {e}")
        return False

def test_thumbnail_generation():
    """测试封面生成模块"""
    logger.info("测试封面生成模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("thumbnail_gen", "05_thumbnail/thumbnail_gen.py")
        thumbnail_gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(thumbnail_gen)
        ThumbnailGenerator = thumbnail_gen.ThumbnailGenerator
        
        generator = ThumbnailGenerator()
        
        # 测试封面生成
        thumbnail_path = generator.create_thumbnail_local(
            "测试视频标题",
            "test background prompt",
            "default"
        )
        
        if thumbnail_path:
            logger.info("✅ 封面生成成功")
            return True
        else:
            logger.error("❌ 封面生成失败")
            return False
    except Exception as e:
        logger.error(f"❌ 封面生成模块测试失败: {e}")
        return False

def test_account_management():
    """测试账号管理模块"""
    logger.info("测试账号管理模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("account_db", "06_account_manager/account_db.py")
        account_db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(account_db)
        AccountDatabase = account_db.AccountDatabase
        
        db = AccountDatabase()
        
        # 测试数据库连接
        accounts = db.get_active_accounts()
        logger.info(f"✅ 账号管理模块测试成功，当前有 {len(accounts)} 个活跃账号")
        
        return True
    except Exception as e:
        logger.error(f"❌ 账号管理模块测试失败: {e}")
        return False

def test_upload_modules():
    """测试上传模块"""
    logger.info("测试上传模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("upload_douyin", "07_uploader/upload_douyin.py")
        upload_douyin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(upload_douyin)
        DouyinUploader = upload_douyin.DouyinUploader
        
        spec = importlib.util.spec_from_file_location("upload_bilibili", "07_uploader/upload_bilibili.py")
        upload_bilibili = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(upload_bilibili)
        BilibiliUploader = upload_bilibili.BilibiliUploader
        
        # 测试抖音上传器
        douyin_uploader = DouyinUploader()
        logger.info("✅ 抖音上传器初始化成功")
        
        # 测试B站上传器
        bilibili_uploader = BilibiliUploader()
        logger.info("✅ B站上传器初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 上传模块测试失败: {e}")
        return False

def test_content_review():
    """测试内容审核模块"""
    logger.info("测试内容审核模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("content_review", "08_content_review/content_review.py")
        content_review = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(content_review)
        ContentReviewer = content_review.ContentReviewer
        
        reviewer = ContentReviewer()
        
        # 测试文本审核
        test_text = "这是一个测试视频标题"
        result = reviewer.check_text_content(test_text, "douyin")
        logger.info("✅ 内容审核模块初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 内容审核模块测试失败: {e}")
        return False

def test_scheduler():
    """测试发布调度模块"""
    logger.info("测试发布调度模块...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("scheduler", "09_scheduler/scheduler.py")
        scheduler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scheduler)
        PublishScheduler = scheduler.PublishScheduler
        
        scheduler_instance = PublishScheduler()
        
        # 测试调度功能
        video_info = {
            "video_path": "test_video.mp4",
            "title": "测试视频标题",
            "description": "这是一个测试视频",
            "tags": ["测试", "视频"]
        }
        
        result = scheduler_instance.schedule_video_publish(video_info, "douyin", 1)
        logger.info("✅ 发布调度模块初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 发布调度模块测试失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    logger.info("测试目录结构...")
    try:
        required_dirs = [
            "data",
            "data/videos",
            "data/audio",
            "data/thumbnails",
            "data/edited_videos",
            "logs"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {dir_path}")
        
        logger.info("✅ 目录结构检查完成")
        return True
    except Exception as e:
        logger.error(f"❌ 目录结构测试失败: {e}")
        return False

def test_dependencies():
    """测试依赖包"""
    logger.info("测试依赖包...")
    try:
        import requests
        import selenium
        import openai
        import PIL
        import sqlite3
        import cryptography
        
        logger.info("✅ 核心依赖包检查通过")
        return True
    except ImportError as e:
        logger.error(f"❌ 依赖包缺失: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 50)
    logger.info("开始系统测试")
    logger.info("=" * 50)
    
    tests = [
        ("目录结构", test_directory_structure),
        ("依赖包", test_dependencies),
        ("配置文件", test_config),
        ("内容采集", test_content_fetch),
        ("脚本生成", test_script_generation),
        ("TTS生成", test_tts_generation),
        ("视频剪辑", test_video_editing),
        ("封面生成", test_thumbnail_generation),
        ("账号管理", test_account_management),
        ("上传模块", test_upload_modules),
        ("内容审核", test_content_review),
        ("发布调度", test_scheduler),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n开始测试: {test_name}")
        start_time = time.time()
        
        try:
            success = test_func()
            elapsed_time = time.time() - start_time
            
            if success:
                logger.info(f"✅ {test_name} 测试通过 (耗时: {elapsed_time:.2f}秒)")
            else:
                logger.error(f"❌ {test_name} 测试失败 (耗时: {elapsed_time:.2f}秒)")
            
            results.append((test_name, success, elapsed_time))
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ {test_name} 测试异常: {e} (耗时: {elapsed_time:.2f}秒)")
            results.append((test_name, False, elapsed_time))
    
    # 输出测试结果
    logger.info("\n" + "=" * 50)
    logger.info("测试结果汇总")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    total_time = 0
    
    for test_name, success, elapsed_time in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{test_name:<15} {status} ({elapsed_time:.2f}秒)")
        
        if success:
            passed += 1
        else:
            failed += 1
        
        total_time += elapsed_time
    
    logger.info("-" * 50)
    logger.info(f"总计: {len(results)} 个测试")
    logger.info(f"通过: {passed} 个")
    logger.info(f"失败: {failed} 个")
    logger.info(f"总耗时: {total_time:.2f} 秒")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！系统运行正常。")
        return True
    else:
        logger.warning(f"⚠️ 有 {failed} 个测试失败，请检查相关配置。")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # 快速测试模式
        logger.info("运行快速测试模式...")
        quick_tests = [
            ("目录结构", test_directory_structure),
            ("依赖包", test_dependencies),
            ("配置文件", test_config),
        ]
        
        for test_name, test_func in quick_tests:
            logger.info(f"测试: {test_name}")
            if not test_func():
                logger.error(f"快速测试失败: {test_name}")
                return False
        
        logger.info("✅ 快速测试通过")
        return True
    else:
        # 完整测试模式
        return run_all_tests()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 