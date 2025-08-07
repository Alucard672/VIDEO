#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型内容采集器
支持从多种来源采集内容，包括API、HTML页面、RSS等
"""

import requests
import json
import logging
import time
import re
import random
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 配置日志
logger = logging.getLogger(__name__)

class EnhancedContentFetcher:
    """增强型内容采集器类"""
    
    def __init__(self, user_agent: str = None, timeout: int = 30, 
                retry_count: int = 3, retry_delay: int = 5):
        """初始化采集器
        
        Args:
            user_agent: 请求头中的User-Agent
            timeout: 请求超时时间（秒）
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        
        # 会话对象，用于保持连接
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
    
    def fetch_from_source(self, source: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """从指定源采集内容
        
        Args:
            source: 采集源配置
            limit: 采集数量限制
            
        Returns:
            采集结果列表
        """
        platform = source.get("platform", "").upper()
        
        try:
            if platform == "API":
                return self._fetch_from_api(source, limit)
            elif platform == "HTML":
                return self._fetch_from_html(source, limit)
            elif platform == "RSS":
                return self._fetch_from_rss(source, limit)
            elif platform == "JSON":
                return self._fetch_from_json_file(source, limit)
            elif platform == "CSV":
                return self._fetch_from_csv_file(source, limit)
            else:
                logger.warning(f"不支持的平台类型: {platform}")
                return []
        
        except Exception as e:
            logger.error(f"从源 {source.get('name')} 采集内容失败: {e}")
            return []
    
    def _make_request(self, url: str, method: str = "GET", 
                     headers: Dict[str, str] = None, 
                     params: Dict[str, Any] = None,
                     data: Dict[str, Any] = None) -> Optional[requests.Response]:
        """发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            headers: 请求头
            params: URL参数
            data: 请求体数据
            
        Returns:
            响应对象，失败则返回None
        """
        # 合并请求头
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)
        
        # 重试机制
        for attempt in range(self.retry_count + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=params,
                    json=data if method.upper() in ["POST", "PUT", "PATCH"] else None,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                return response
            
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt+1}/{self.retry_count+1}): {url} - {e}")
                
                if attempt < self.retry_count:
                    # 随机延迟，避免同时重试
                    delay = self.retry_delay + random.uniform(0, 2)
                    time.sleep(delay)
                else:
                    logger.error(f"请求失败，已达到最大重试次数: {url}")
                    return None
    
    def _fetch_from_api(self, source: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """从API采集内容
        
        Args:
            source: API源配置
            limit: 采集数量限制
            
        Returns:
            采集结果列表
        """
        url = source.get("url")
        if not url:
            logger.error("API源URL不能为空")
            return []
        
        # 准备请求参数
        headers = {}
        params = {}
        
        # 添加API密钥
        api_key = source.get("api_key")
        if api_key:
            # 根据不同API的要求，可能在请求头或参数中
            if source.get("api_key_in_header", False):
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                params["api_key"] = api_key
        
        # 添加分页参数
        if source.get("pagination_supported", True):
            params[source.get("limit_param", "limit")] = limit
            params[source.get("offset_param", "offset")] = 0
        
        # 发送请求
        response = self._make_request(url, headers=headers, params=params)
        if not response:
            return []
        
        # 解析响应
        try:
            data = response.json()
            
            # 获取内容路径
            content_path = source.get("content_path")
            if content_path:
                # 支持多级路径，如 "data.articles"
                for key in content_path.split("."):
                    if key in data:
                        data = data[key]
                    else:
                        logger.warning(f"内容路径 {content_path} 在响应中不存在")
                        return []
            
            # 确保数据是列表
            if not isinstance(data, list):
                logger.warning("API响应不是列表格式")
                return []
            
            # 限制数量
            data = data[:limit]
            
            # 提取字段
            results = []
            for item in data:
                # 提取标题
                title = self._extract_field(item, source.get("title_field", "title"))
                
                # 提取内容
                content = self._extract_field(item, source.get("content_field", "content"))
                
                # 提取URL
                url = self._extract_field(item, source.get("url_field", "url"))
                
                # 提取日期
                date = self._extract_field(item, source.get("date_field", "published_at"))
                
                # 提取分类
                category = self._extract_field(item, source.get("category_field")) or source.get("category", "")
                
                # 提取标签
                tags_field = source.get("tags_field")
                tags = self._extract_field(item, tags_field) if tags_field else []
                
                # 如果标签是字符串，尝试分割
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(",")]
                
                # 构建结果
                result = {
                    "title": title,
                    "content": content,
                    "url": url,
                    "publish_date": date,
                    "category": category,
                    "tags": tags,
                    "source_name": source.get("name", ""),
                    "source_type": "API"
                }
                
                results.append(result)
            
            logger.info(f"从API源 {source.get('name')} 采集了 {len(results)} 条内容")
            return results
        
        except json.JSONDecodeError:
            logger.error("API响应不是有效的JSON格式")
            return []
        
        except Exception as e:
            logger.error(f"解析API响应失败: {e}")
            return []
    
    def _fetch_from_html(self, source: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """从HTML页面采集内容
        
        Args:
            source: HTML源配置
            limit: 采集数量限制
            
        Returns:
            采集结果列表
        """
        url = source.get("url")
        if not url:
            logger.error("HTML源URL不能为空")
            return []
        
        # 发送请求
        response = self._make_request(url)
        if not response:
            return []
        
        # 解析HTML
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 获取选择器类型
            selector_type = source.get("selector_type", "css").lower()
            
            # 获取列表选择器
            list_selector = source.get("list_selector")
            if not list_selector:
                logger.error("列表选择器不能为空")
                return []
            
            # 查找所有列表项
            if selector_type == "css":
                items = soup.select(list_selector)
            elif selector_type == "xpath":
                # BeautifulSoup不直接支持XPath，这里简化处理
                logger.warning("BeautifulSoup不支持XPath，使用CSS选择器代替")
                items = soup.select(list_selector)
            else:
                logger.error(f"不支持的选择器类型: {selector_type}")
                return []
            
            # 限制数量
            items = items[:limit]
            
            # 提取内容
            results = []
            for item in items:
                try:
                    # 提取标题
                    title_selector = source.get("title_selector")
                    title_element = item.select_one(title_selector) if title_selector else None
                    title = title_element.get_text().strip() if title_element else ""
                    
                    # 提取内容
                    content_selector = source.get("content_selector")
                    content_element = item.select_one(content_selector) if content_selector else None
                    content = content_element.get_text().strip() if content_element else ""
                    
                    # 提取URL
                    url_selector = source.get("url_selector")
                    url_element = item.select_one(url_selector) if url_selector else None
                    
                    if url_element:
                        url_attribute = source.get("url_attribute", "href")
                        item_url = url_element.get(url_attribute, "")
                        # 处理相对URL
                        item_url = urljoin(url, item_url)
                    else:
                        item_url = ""
                    
                    # 提取日期
                    date_selector = source.get("date_selector")
                    date_element = item.select_one(date_selector) if date_selector else None
                    date = date_element.get_text().strip() if date_element else ""
                    
                    # 提取分类
                    category = source.get("category", "")
                    
                    # 构建结果
                    result = {
                        "title": title,
                        "content": content,
                        "url": item_url,
                        "publish_date": date,
                        "category": category,
                        "tags": [],
                        "source_name": source.get("name", ""),
                        "source_type": "HTML"
                    }
                    
                    results.append(result)
                
                except Exception as e:
                    logger.warning(f"提取HTML内容项失败: {e}")
                    continue
            
            logger.info(f"从HTML源 {source.get('name')} 采集了 {len(results)} 条内容")
            return results
        
        except Exception as e:
            logger.error(f"解析HTML页面失败: {e}")
            return []
    
    def _fetch_from_rss(self, source: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """从RSS源采集内容
        
        Args:
            source: RSS源配置
            limit: 采集数量限制
            
        Returns:
            采集结果列表
        """
        url = source.get("url")
        if not url:
            logger.error("RSS源URL不能为空")
            return []
        
        try:
            # 解析RSS
            feed = feedparser.parse(url)
            
            if not feed.entries:
                logger.warning(f"RSS源 {url} 没有条目")
                return []
            
            # 限制数量
            entries = feed.entries[:limit]
            
            # 提取内容
            results = []
            for entry in entries:
                # 提取标题
                title = entry.get("title", "")
                
                # 提取内容
                content = ""
                if "content" in entry:
                    content = entry.content[0].value
                elif "summary" in entry:
                    content = entry.summary
                elif "description" in entry:
                    content = entry.description
                
                # 提取URL
                item_url = entry.get("link", "")
                
                # 提取日期
                date = ""
                if "published" in entry:
                    date = entry.published
                elif "updated" in entry:
                    date = entry.updated
                
                # 提取分类
                category = source.get("category", "")
                if "tags" in entry:
                    for tag in entry.tags:
                        if tag.term:
                            category = tag.term
                            break
                
                # 提取标签
                tags = []
                if "tags" in entry:
                    tags = [tag.term for tag in entry.tags if tag.term]
                
                # 构建结果
                result = {
                    "title": title,
                    "content": content,
                    "url": item_url,
                    "publish_date": date,
                    "category": category,
                    "tags": tags,
                    "source_name": source.get("name", ""),
                    "source_type": "RSS"
                }
                
                results.append(result)
            
            logger.info(f"从RSS源 {source.get('name')} 采集了 {len(results)} 条内容")
            return results
        
        except Exception as e:
            logger.error(f"解析RSS源失败: {e}")
            return []
    
    def _fetch_from_json_file(self, source: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """从JSON文件采集内容
        
        Args:
            source: JSON文件源配置
            limit: 采集数量限制
            
        Returns:
            采集结果列表
        """
        url = source.get("url")
        if not url:
            logger.error("JSON文件URL不能为空")
            return []
        
        # 发送请求
        response = self._make_request(url)
        if not response:
            return []
        
        # 解析JSON
        try:
            data = response.json()
            
            # 获取内容路径
            content_path = source.get("content_path")
            if content_path:
                # 支持多级路径，如 "data.articles"
                for key in content_path.split("."):
                    if key in data:
                        data = data[key]
                    else:
                        logger.warning(f"内容路径 {content_path} 在JSON中不存在")
                        return []
            
            # 确保数据是列表
            if not isinstance(data, list):
                logger.warning("JSON数据不是列表格式")
                return []
            
            # 限制数量
            data = data[:limit]
            
            # 提取字段
            results = []
            for item in data:
                # 提取标题
                title = self._extract_field(item, source.get("title_field", "title"))
                
                # 提取内容
                content = self._extract_field(item, source.get("content_field", "content"))
                
                # 提取URL
                url = self._extract_field(item, source.get("url_field", "url"))
                
                # 提取日期
                date = self._extract_field(item, source.get("date_field", "published_at"))
                
                # 提取分类
                category = self._extract_field(item, source.get("category_field")) or source.get("category", "")
                
                # 提取标签
                tags_field = source.get("tags_field")
                tags = self._extract_field(item, tags_field) if tags_field else []
                
                # 如果标签是字符串，尝试分割
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(",")]
                
                # 构建结果
                result = {
                    "title": title,
                    "content": content,
                    "url": url,
                    "publish_date": date,
                    "category": category,
                    "tags": tags,
                    "source_name": source.get("name", ""),
                    "source_type": "JSON"
                }
                
                results.append(result)
            
            logger.info(f"从JSON文件源 {source.get('name')} 采集了 {len(results)} 条内容")
            return results
        
        except json.JSONDecodeError:
            logger.error("JSON文件格式无效")
            return []
        
        except Exception as e:
            logger.error(f"解析JSON文件失败: {e}")
            return []
    
    def _fetch_from_csv_file(self, source: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """从CSV文件采集内容
        
        Args:
            source: CSV文件源配置
            limit: 采集数量限制
            
        Returns:
            采集结果列表
        """
        url = source.get("url")
        if not url:
            logger.error("CSV文件URL不能为空")
            return []
        
        # 发送请求
        response = self._make_request(url)
        if not response:
            return []
        
        # 解析CSV
        try:
            import csv
            from io import StringIO
            
            # 获取分隔符
            delimiter = source.get("delimiter", ",")
            
            # 解析CSV
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data, delimiter=delimiter)
            
            # 提取内容
            results = []
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                
                # 提取标题
                title_column = source.get("title_column", "title")
                title = row.get(title_column, "")
                
                # 提取内容
                content_column = source.get("content_column", "content")
                content = row.get(content_column, "")
                
                # 提取URL
                url_column = source.get("url_column", "url")
                item_url = row.get(url_column, "")
                
                # 提取日期
                date_column = source.get("date_column", "date")
                date = row.get(date_column, "")
                
                # 提取分类
                category_column = source.get("category_column")
                category = row.get(category_column, "") if category_column else source.get("category", "")
                
                # 提取标签
                tags_column = source.get("tags_column")
                tags = []
                if tags_column and tags_column in row:
                    tags_str = row[tags_column]
                    if tags_str:
                        tags = [tag.strip() for tag in tags_str.split(",")]
                
                # 构建结果
                result = {
                    "title": title,
                    "content": content,
                    "url": item_url,
                    "publish_date": date,
                    "category": category,
                    "tags": tags,
                    "source_name": source.get("name", ""),
                    "source_type": "CSV"
                }
                
                results.append(result)
            
            logger.info(f"从CSV文件源 {source.get('name')} 采集了 {len(results)} 条内容")
            return results
        
        except Exception as e:
            logger.error(f"解析CSV文件失败: {e}")
            return []
    
    def _extract_field(self, data: Dict[str, Any], field: str) -> Any:
        """从数据中提取字段值
        
        Args:
            data: 数据字典
            field: 字段名，支持点号分隔的多级路径
            
        Returns:
            字段值，不存在则返回空字符串
        """
        if not field:
            return ""
        
        # 处理多级路径
        parts = field.split(".")
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return ""
        
        return value
    
    def fetch_content_details(self, url: str, selectors: Dict[str, str] = None) -> Dict[str, Any]:
        """获取内容详情
        
        Args:
            url: 内容URL
            selectors: 选择器配置
            
        Returns:
            内容详情
        """
        if not url:
            logger.error("内容URL不能为空")
            return {}
        
        # 发送请求
        response = self._make_request(url)
        if not response:
            return {}
        
        # 如果没有提供选择器，返回原始内容
        if not selectors:
            return {
                "url": url,
                "html": response.text,
                "title": self._extract_title_from_html(response.text),
                "content": self._extract_content_from_html(response.text)
            }
        
        # 解析HTML
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            
            result = {"url": url}
            
            # 提取各字段
            for field, selector in selectors.items():
                element = soup.select_one(selector)
                result[field] = element.get_text().strip() if element else ""
            
            return result
        
        except Exception as e:
            logger.error(f"解析内容详情失败: {e}")
            return {"url": url}
    
    def _extract_title_from_html(self, html: str) -> str:
        """从HTML中提取标题
        
        Args:
            html: HTML内容
            
        Returns:
            标题
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 尝试从title标签获取
            title_tag = soup.title
            if title_tag:
                return title_tag.get_text().strip()
            
            # 尝试从h1标签获取
            h1_tag = soup.h1
            if h1_tag:
                return h1_tag.get_text().strip()
            
            return ""
        
        except Exception:
            return ""
    
    def _extract_content_from_html(self, html: str) -> str:
        """从HTML中提取正文内容
        
        Args:
            html: HTML内容
            
        Returns:
            正文内容
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取文本
            text = soup.get_text()
            
            # 处理空白
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            return text
        
        except Exception:
            return ""
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """从内容中提取元数据
        
        Args:
            content: 内容文本
            
        Returns:
            元数据字典
        """
        metadata = {
            "keywords": [],
            "entities": [],
            "summary": "",
            "language": "zh-CN"  # 默认中文
        }
        
        try:
            # 提取关键词（简单实现，实际应使用NLP库）
            words = re.findall(r'\b\w+\b', content.lower())
            word_count = {}
            
            for word in words:
                if len(word) > 1:  # 忽略单字符词
                    word_count[word] = word_count.get(word, 0) + 1
            
            # 按出现频率排序
            sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
            
            # 取前10个作为关键词
            metadata["keywords"] = [word for word, _ in sorted_words[:10]]
            
            # 生成摘要（取前200个字符）
            metadata["summary"] = content[:200] + "..." if len(content) > 200 else content
            
            return metadata
        
        except Exception as e:
            logger.error(f"提取元数据失败: {e}")
            return metadata
    
    def close(self):
        """关闭会话"""
        self.session.close()

# 测试代码
if __name__ == "__main__":
    print("=== 增强型内容采集器测试 ===")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建采集器
    fetcher = EnhancedContentFetcher()
    
    # 测试API采集
    api_source = {
        "name": "测试API",
        "platform": "API",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "description": "测试API数据源",
        "category": "测试",
        "title_field": "title",
        "content_field": "body",
        "url_field": "id",  # 这里用id代替url
        "enabled": True
    }
    
    print("\n测试API采集:")
    api_results = fetcher.fetch_from_source(api_source, limit=3)
    for i, result in enumerate(api_results):
        print(f"结果 {i+1}:")
        print(f"  标题: {result['title']}")
        print(f"  内容: {result['content'][:50]}...")
    
    # 测试HTML采集
    html_source = {
        "name": "测试HTML",
        "platform": "HTML",
        "url": "https://news.baidu.com/",
        "description": "测试HTML数据源",
        "category": "新闻",
        "selector_type": "css",
        "list_selector": ".hotnews li",
        "title_selector": "a",
        "url_selector": "a",
        "url_attribute": "href",
        "enabled": True
    }
    
    print("\n测试HTML采集:")
    html_results = fetcher.fetch_from_source(html_source, limit=3)
    for i, result in enumerate(html_results):
        print(f"结果 {i+1}:")
        print(f"  标题: {result['title']}")
        print(f"  URL: {result['url']}")
    
    # 关闭采集器
    fetcher.close()
    
    print("\n增强型内容采集器测试完成")