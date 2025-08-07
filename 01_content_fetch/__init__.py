#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容采集模块
"""

from .fetch_news import NewsFetcher
from .fetch_videos import VideoFetcher

__all__ = ['NewsFetcher', 'VideoFetcher'] 