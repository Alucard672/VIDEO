#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容采集配置管理
管理内容采集源、分类和配置
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 默认采集配置
DEFAULT_FETCH_CONFIG = {
    "fetch_interval": 3600,  # 默认采集间隔（秒）
    "fetch_limit": 20,       # 默认单源采集数量限制
    "timeout": 30,           # 默认请求超时（秒）
    "retry_count": 3,        # 默认重试次数
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 默认内容源
DEFAULT_CONTENT_SOURCES = [
    {
        "id": 1,
        "name": "百度新闻",
        "platform": "HTML",
        "url": "https://news.baidu.com/",
        "description": "百度新闻聚合页",
        "category": "新闻",
        "selector_type": "css",
        "list_selector": ".hotnews li",
        "title_selector": "a",
        "url_selector": "a",
        "url_attribute": "href",
        "fetch_limit": 20,
        "fetch_interval": 3600,
        "enabled": True
    },
    {
        "id": 2,
        "name": "知乎热榜",
        "platform": "HTML",
        "url": "https://www.zhihu.com/hot",
        "description": "知乎热门话题",
        "category": "社交",
        "selector_type": "css",
        "list_selector": ".HotItem",
        "title_selector": ".HotItem-title",
        "url_selector": ".HotItem-content a",
        "url_attribute": "href",
        "fetch_limit": 20,
        "fetch_interval": 3600,
        "enabled": True
    },
    {
        "id": 3,
        "name": "GitHub Trending",
        "platform": "HTML",
        "url": "https://github.com/trending",
        "description": "GitHub 趋势项目",
        "category": "技术",
        "selector_type": "css",
        "list_selector": "article.Box-row",
        "title_selector": "h2 a",
        "content_selector": "p",
        "url_selector": "h2 a",
        "url_attribute": "href",
        "fetch_limit": 15,
        "fetch_interval": 86400,
        "enabled": True
    },
    {
        "id": 4,
        "name": "JSONPlaceholder API",
        "platform": "API",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "description": "测试API数据源",
        "category": "测试",
        "title_field": "title",
        "content_field": "body",
        "url_field": "id",
        "fetch_limit": 10,
        "fetch_interval": 3600,
        "enabled": True
    }
]

# 默认分类
DEFAULT_CATEGORIES = [
    {"id": 1, "name": "新闻", "description": "新闻资讯"},
    {"id": 2, "name": "技术", "description": "技术文章"},
    {"id": 3, "name": "社交", "description": "社交媒体内容"},
    {"id": 4, "name": "娱乐", "description": "娱乐资讯"},
    {"id": 5, "name": "测试", "description": "测试内容"}
]

class ContentFetchConfig:
    """内容采集配置类"""
    
    def __init__(self, config_dir: str = None):
        """初始化配置
        
        Args:
            config_dir: 配置目录路径
        """
        # 配置目录
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), "config")
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 配置文件路径
        self.sources_file = os.path.join(self.config_dir, "content_sources.json")
        self.categories_file = os.path.join(self.config_dir, "content_categories.json")
        self.config_file = os.path.join(self.config_dir, "fetch_config.json")
        
        # 初始化配置
        self._init_config()
    
    def _init_config(self):
        """初始化配置文件"""
        # 初始化内容源
        if not os.path.exists(self.sources_file):
            self.save_sources(DEFAULT_CONTENT_SOURCES)
        
        # 初始化分类
        if not os.path.exists(self.categories_file):
            self.save_categories(DEFAULT_CATEGORIES)
        
        # 初始化采集配置
        if not os.path.exists(self.config_file):
            self.save_config(DEFAULT_FETCH_CONFIG)
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """获取所有内容源
        
        Returns:
            内容源列表
        """
        try:
            if os.path.exists(self.sources_file):
                with open(self.sources_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return DEFAULT_CONTENT_SOURCES
        except Exception as e:
            logger.error(f"读取内容源配置失败: {e}")
            return DEFAULT_CONTENT_SOURCES
    
    def get_source_by_id(self, source_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取内容源
        
        Args:
            source_id: 内容源ID
            
        Returns:
            内容源配置，不存在则返回None
        """
        sources = self.get_sources()
        for source in sources:
            if source.get("id") == source_id:
                return source
        return None
    
    def save_sources(self, sources: List[Dict[str, Any]]) -> bool:
        """保存内容源配置
        
        Args:
            sources: 内容源列表
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.sources_file, "w", encoding="utf-8") as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存内容源配置失败: {e}")
            return False
    
    def add_source(self, source: Dict[str, Any]) -> int:
        """添加内容源
        
        Args:
            source: 内容源配置
            
        Returns:
            新增内容源ID，失败则返回-1
        """
        try:
            sources = self.get_sources()
            
            # 生成新ID
            max_id = max([s.get("id", 0) for s in sources], default=0)
            new_id = max_id + 1
            
            # 设置ID
            source["id"] = new_id
            
            # 添加到列表
            sources.append(source)
            
            # 保存
            if self.save_sources(sources):
                return new_id
            return -1
        except Exception as e:
            logger.error(f"添加内容源失败: {e}")
            return -1
    
    def update_source(self, source_id: int, source: Dict[str, Any]) -> bool:
        """更新内容源
        
        Args:
            source_id: 内容源ID
            source: 更新的内容源配置
            
        Returns:
            是否更新成功
        """
        try:
            sources = self.get_sources()
            
            for i, s in enumerate(sources):
                if s.get("id") == source_id:
                    # 保留ID
                    source["id"] = source_id
                    sources[i] = source
                    return self.save_sources(sources)
            
            return False
        except Exception as e:
            logger.error(f"更新内容源失败: {e}")
            return False
    
    def delete_source(self, source_id: int) -> bool:
        """删除内容源
        
        Args:
            source_id: 内容源ID
            
        Returns:
            是否删除成功
        """
        try:
            sources = self.get_sources()
            
            for i, source in enumerate(sources):
                if source.get("id") == source_id:
                    del sources[i]
                    return self.save_sources(sources)
            
            return False
        except Exception as e:
            logger.error(f"删除内容源失败: {e}")
            return False
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类
        
        Returns:
            分类列表
        """
        try:
            if os.path.exists(self.categories_file):
                with open(self.categories_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return DEFAULT_CATEGORIES
        except Exception as e:
            logger.error(f"读取分类配置失败: {e}")
            return DEFAULT_CATEGORIES
    
    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            分类配置，不存在则返回None
        """
        categories = self.get_categories()
        for category in categories:
            if category.get("id") == category_id:
                return category
        return None
    
    def save_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """保存分类配置
        
        Args:
            categories: 分类列表
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump(categories, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存分类配置失败: {e}")
            return False
    
    def add_category(self, category: Dict[str, Any]) -> int:
        """添加分类
        
        Args:
            category: 分类配置
            
        Returns:
            新增分类ID，失败则返回-1
        """
        try:
            categories = self.get_categories()
            
            # 生成新ID
            max_id = max([c.get("id", 0) for c in categories], default=0)
            new_id = max_id + 1
            
            # 设置ID
            category["id"] = new_id
            
            # 添加到列表
            categories.append(category)
            
            # 保存
            if self.save_categories(categories):
                return new_id
            return -1
        except Exception as e:
            logger.error(f"添加分类失败: {e}")
            return -1
    
    def update_category(self, category_id: int, category: Dict[str, Any]) -> bool:
        """更新分类
        
        Args:
            category_id: 分类ID
            category: 更新的分类配置
            
        Returns:
            是否更新成功
        """
        try:
            categories = self.get_categories()
            
            for i, c in enumerate(categories):
                if c.get("id") == category_id:
                    # 保留ID
                    category["id"] = category_id
                    categories[i] = category
                    return self.save_categories(categories)
            
            return False
        except Exception as e:
            logger.error(f"更新分类失败: {e}")
            return False
    
    def delete_category(self, category_id: int) -> bool:
        """删除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            是否删除成功
        """
        try:
            categories = self.get_categories()
            
            for i, category in enumerate(categories):
                if category.get("id") == category_id:
                    del categories[i]
                    return self.save_categories(categories)
            
            return False
        except Exception as e:
            logger.error(f"删除分类失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取采集配置
        
        Returns:
            采集配置
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return DEFAULT_FETCH_CONFIG
        except Exception as e:
            logger.error(f"读取采集配置失败: {e}")
            return DEFAULT_FETCH_CONFIG
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存采集配置
        
        Args:
            config: 采集配置
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存采集配置失败: {e}")
            return False
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """更新采集配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            是否更新成功
        """
        try:
            config = self.get_config()
            config.update(config_updates)
            return self.save_config(config)
        except Exception as e:
            logger.error(f"更新采集配置失败: {e}")
            return False

# 导出默认内容源
CONTENT_SOURCES = DEFAULT_CONTENT_SOURCES

# 测试代码
if __name__ == "__main__":
    print("=== 内容采集配置测试 ===")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建配置管理器
    config = ContentFetchConfig()
    
    # 获取内容源
    sources = config.get_sources()
    print(f"内容源数量: {len(sources)}")
    
    # 获取分类
    categories = config.get_categories()
    print(f"分类数量: {len(categories)}")
    
    # 获取采集配置
    fetch_config = config.get_config()
    print(f"采集间隔: {fetch_config.get('fetch_interval')} 秒")
    
    print("内容采集配置测试完成")