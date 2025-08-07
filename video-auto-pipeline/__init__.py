#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化流水线项目
这个文件自动导入所有模块，使它们可以通过标准Python导入语法访问
"""

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
