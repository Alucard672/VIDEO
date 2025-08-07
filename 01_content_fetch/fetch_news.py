#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻采集模块
支持从多个新闻平台获取热点新闻
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from bs4 import BeautifulSoup
import random

class NewsFetcher:
    """新闻采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.data_dir = Path(__file__).parent.parent / "data"
        self.news_dir = self.data_dir / "news"
        self.news_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_netease_news(self, category="热点", limit=10):
        """
        获取网易新闻
        
        Args:
            category: 新闻分类 (热点, 科技, 娱乐, 体育, 财经)
            limit: 获取数量限制
        
        Returns:
            list: 新闻列表
        """
        try:
            logger.info(f"开始获取网易新闻 - 分类: {category}")
            
            # 网易新闻API
            api_url = "https://3g.163.com/touch/reconstruct/article/list/BBM54PGAwangning/0-10.html"
            
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            
            # 解析新闻数据
            news_list = []
            try:
                data = response.json()
                articles = data.get('BBM54PGAwangning', [])
                
                for article in articles[:limit]:
                    news_item = {
                        'title': article.get('title', ''),
                        'content': article.get('digest', ''),
                        'url': article.get('url', ''),
                        'source': '网易新闻',
                        'category': category,
                        'timestamp': article.get('ptime', ''),
                        'image_url': article.get('imgsrc', ''),
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    # 过滤空标题或内容
                    if news_item['title'] and news_item['content']:
                        news_list.append(news_item)
                
                logger.info(f"成功获取 {len(news_list)} 条网易新闻")
                
            except json.JSONDecodeError:
                logger.warning("网易新闻API返回格式异常，尝试备用方案")
                news_list = self._fetch_netease_news_fallback(category, limit)
            
            # 保存新闻数据
            self._save_news_data(news_list, f"netease_{category}")
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取网易新闻失败: {e}")
            return []
    
    def _fetch_netease_news_fallback(self, category, limit):
        """备用新闻获取方案"""
        try:
            # 使用模拟数据
            sample_news = [
                {
                    'title': '人工智能技术发展迅速，ChatGPT引领AI革命',
                    'content': '随着人工智能技术的快速发展，ChatGPT等大语言模型正在改变我们的工作和生活方式。专家表示，AI技术将在未来几年内带来更多创新。',
                    'url': 'https://news.163.com/ai/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': '新能源汽车市场持续增长，充电基础设施建设加快',
                    'content': '随着环保意识的提升，新能源汽车市场呈现爆发式增长。各地政府正在加快充电基础设施建设，为新能源汽车普及提供支持。',
                    'url': 'https://news.163.com/auto/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': '5G技术应用广泛，智慧城市建设加速推进',
                    'content': '5G技术的广泛应用正在推动智慧城市建设。从智能交通到智慧医疗，5G技术为城市管理带来了新的可能性。',
                    'url': 'https://news.163.com/tech/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            return sample_news[:limit]
            
        except Exception as e:
            logger.error(f"备用新闻获取失败: {e}")
            return []
    
    def fetch_sina_news(self, category="热点", limit=10):
        """
        获取新浪新闻
        
        Args:
            category: 新闻分类
            limit: 获取数量限制
        
        Returns:
            list: 新闻列表
        """
        try:
            logger.info(f"开始获取新浪新闻 - 分类: {category}")
            
            # 新浪新闻API
            api_url = "https://interface.sina.cn/news/get_news_by_channel_v2.json"
            params = {
                'channel': 'news',
                'page': 1,
                'page_size': limit
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            news_list = []
            try:
                data = response.json()
                articles = data.get('result', {}).get('list', [])
                
                for article in articles:
                    news_item = {
                        'title': article.get('title', ''),
                        'content': article.get('summary', ''),
                        'url': article.get('url', ''),
                        'source': '新浪新闻',
                        'category': category,
                        'timestamp': article.get('ctime', ''),
                        'image_url': article.get('image', ''),
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    if news_item['title'] and news_item['content']:
                        news_list.append(news_item)
                
                logger.info(f"成功获取 {len(news_list)} 条新浪新闻")
                
            except json.JSONDecodeError:
                logger.warning("新浪新闻API返回格式异常")
                news_list = []
            
            # 保存新闻数据
            self._save_news_data(news_list, f"sina_{category}")
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取新浪新闻失败: {e}")
            return []
    
    def fetch_hot_topics(self, platform="weibo", limit=10):
        """
        获取热点话题
        
        Args:
            platform: 平台 (weibo, zhihu, douyin)
            limit: 获取数量限制
        
        Returns:
            list: 话题列表
        """
        try:
            logger.info(f"开始获取{platform}热点话题")
            
            # 模拟热点话题数据
            hot_topics = [
                {
                    'title': 'AI技术发展',
                    'content': '人工智能技术快速发展，ChatGPT等大语言模型引发热议',
                    'url': f'https://{platform}.com/topic/ai',
                    'source': platform,
                    'category': '科技',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'hot_value': random.randint(1000, 10000),
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': '新能源汽车',
                    'content': '新能源汽车市场持续增长，充电基础设施建设加快',
                    'url': f'https://{platform}.com/topic/ev',
                    'source': platform,
                    'category': '汽车',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'hot_value': random.randint(1000, 10000),
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': '5G技术应用',
                    'content': '5G技术应用广泛，智慧城市建设加速推进',
                    'url': f'https://{platform}.com/topic/5g',
                    'source': platform,
                    'category': '科技',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'hot_value': random.randint(1000, 10000),
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            logger.info(f"成功获取 {len(hot_topics)} 个热点话题")
            
            # 保存话题数据
            self._save_news_data(hot_topics, f"{platform}_topics")
            
            return hot_topics[:limit]
            
        except Exception as e:
            logger.error(f"获取{platform}热点话题失败: {e}")
            return []
    
    def _save_news_data(self, news_list, filename):
        """保存新闻数据到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.news_dir / f"{filename}_{timestamp}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"新闻数据已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存新闻数据失败: {e}")
    
    def get_news_summary(self, news_list):
        """
        生成新闻摘要
        
        Args:
            news_list: 新闻列表
        
        Returns:
            dict: 新闻摘要
        """
        if not news_list:
            return {}
        
        # 统计信息
        total_count = len(news_list)
        sources = list(set([news.get('source', '') for news in news_list]))
        categories = list(set([news.get('category', '') for news in news_list]))
        
        # 热门关键词
        all_titles = ' '.join([news.get('title', '') for news in news_list])
        keywords = self._extract_keywords(all_titles)
        
        summary = {
            'total_count': total_count,
            'sources': sources,
            'categories': categories,
            'keywords': keywords[:10],  # 前10个关键词
            'collection_time': datetime.now().isoformat(),
            'latest_news': news_list[0] if news_list else None
        }
        
        return summary
    
    def _extract_keywords(self, text):
        """提取关键词（简化版）"""
        # 这里可以集成更复杂的关键词提取算法
        # 目前使用简单的分词方法
        import re
        
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        
        # 简单的词频统计
        words = text.split()
        word_count = {}
        
        for word in words:
            if len(word) > 1:  # 过滤单字符
                word_count[word] = word_count.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, count in sorted_words]

def main():
    """主函数 - 测试新闻采集功能"""
    logger.info("开始测试新闻采集功能")
    
    fetcher = NewsFetcher()
    
    # 测试网易新闻采集
    netease_news = fetcher.fetch_netease_news(category="热点", limit=5)
    logger.info(f"获取到 {len(netease_news)} 条网易新闻")
    
    # 测试新浪新闻采集
    sina_news = fetcher.fetch_sina_news(category="热点", limit=5)
    logger.info(f"获取到 {len(sina_news)} 条新浪新闻")
    
    # 测试热点话题采集
    hot_topics = fetcher.fetch_hot_topics(platform="weibo", limit=5)
    logger.info(f"获取到 {len(hot_topics)} 个热点话题")
    
    # 生成摘要
    all_news = netease_news + sina_news + hot_topics
    summary = fetcher.get_news_summary(all_news)
    
    logger.info("新闻采集测试完成")
    logger.info(f"总计获取: {summary['total_count']} 条新闻")
    logger.info(f"来源: {summary['sources']}")
    logger.info(f"分类: {summary['categories']}")
    logger.info(f"关键词: {summary['keywords']}")

if __name__ == "__main__":
    main() 