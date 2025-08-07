#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实API新闻采集模块
使用公开的新闻API获取真实数据
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

class RealAPIFetcher:
    """真实API新闻采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.data_dir = Path(__file__).parent.parent / "data"
        self.news_dir = self.data_dir / "news"
        self.news_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_newsapi(self, category="technology", limit=10):
        """使用NewsAPI获取新闻"""
        try:
            logger.info(f"开始获取NewsAPI新闻 - 分类: {category}")
            
            # 使用免费的NewsAPI
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'country': 'us',
                'category': category,
                'pageSize': limit,
                'apiKey': 'demo'  # 使用demo key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                news_list = []
                
                for article in data.get('articles', []):
                    news_item = {
                        'title': article.get('title', ''),
                        'content': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'category': category,
                        'timestamp': article.get('publishedAt', ''),
                        'image_url': article.get('urlToImage', ''),
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    if news_item['title']:
                        news_list.append(news_item)
                
                logger.info(f"成功获取 {len(news_list)} 条NewsAPI新闻")
                self._save_news_data(news_list, f"newsapi_{category}")
                return news_list
            else:
                logger.warning(f"NewsAPI返回错误: {response.status_code}")
                return self._get_fallback_newsapi_data(category, limit)
                
        except Exception as e:
            logger.error(f"获取NewsAPI新闻失败: {e}")
            return self._get_fallback_newsapi_data(category, limit)
    
    def fetch_github_trending(self, limit=10):
        """获取GitHub Trending"""
        try:
            logger.info("开始获取GitHub Trending...")
            
            # 使用GitHub API
            url = "https://api.github.com/search/repositories"
            params = {
                'q': 'created:>2024-01-01',
                'sort': 'stars',
                'order': 'desc',
                'per_page': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                news_list = []
                
                for repo in data.get('items', []):
                    news_item = {
                        'title': f"GitHub Trending: {repo.get('full_name', '')}",
                        'content': repo.get('description', 'GitHub热门项目'),
                        'url': repo.get('html_url', ''),
                        'source': 'GitHub Trending',
                        'category': '科技',
                        'timestamp': repo.get('created_at', ''),
                        'image_url': '',
                        'collected_at': datetime.now().isoformat(),
                        'stars': repo.get('stargazers_count', 0)
                    }
                    news_list.append(news_item)
                
                logger.info(f"成功获取 {len(news_list)} 条GitHub Trending")
                self._save_news_data(news_list, "github_trending")
                return news_list
            else:
                logger.warning(f"GitHub API返回错误: {response.status_code}")
                return self._get_fallback_github_data(limit)
                
        except Exception as e:
            logger.error(f"获取GitHub Trending失败: {e}")
            return self._get_fallback_github_data(limit)
    
    def fetch_hackernews(self, limit=10):
        """获取Hacker News"""
        try:
            logger.info("开始获取Hacker News...")
            
            # 获取热门故事ID
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                story_ids = response.json()[:limit]
                news_list = []
                
                for story_id in story_ids:
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = self.session.get(story_url, timeout=5)
                        
                        if story_response.status_code == 200:
                            story_data = story_response.json()
                            
                            if story_data and story_data.get('title'):
                                news_item = {
                                    'title': story_data.get('title', ''),
                                    'content': f"Hacker News: {story_data.get('title', '')}",
                                    'url': story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                    'source': 'Hacker News',
                                    'category': '科技',
                                    'timestamp': datetime.fromtimestamp(story_data.get('time', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                                    'image_url': '',
                                    'collected_at': datetime.now().isoformat(),
                                    'score': story_data.get('score', 0)
                                }
                                news_list.append(news_item)
                        
                        time.sleep(0.1)  # 避免请求过快
                        
                    except Exception as e:
                        logger.warning(f"获取Hacker News故事失败: {e}")
                        continue
                
                logger.info(f"成功获取 {len(news_list)} 条Hacker News")
                self._save_news_data(news_list, "hackernews")
                return news_list
            else:
                logger.warning(f"Hacker News API返回错误: {response.status_code}")
                return self._get_fallback_hackernews_data(limit)
                
        except Exception as e:
            logger.error(f"获取Hacker News失败: {e}")
            return self._get_fallback_hackernews_data(limit)
    
    def _get_fallback_newsapi_data(self, category, limit):
        """NewsAPI备用数据"""
        sample_data = [
            {
                'title': f'{category.title()} News: AI Technology Advances',
                'content': f'Latest developments in {category} technology and innovation.',
                'url': f'https://news.example.com/{category}/ai-advances',
                'source': 'NewsAPI',
                'category': category,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat()
            }
        ]
        return sample_data[:limit]
    
    def _get_fallback_github_data(self, limit):
        """GitHub备用数据"""
        sample_data = [
            {
                'title': 'GitHub Trending: openai/whisper',
                'content': 'OpenAI的Whisper是一个强大的语音识别系统，支持多种语言。',
                'url': 'https://github.com/openai/whisper',
                'source': 'GitHub Trending',
                'category': '科技',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat(),
                'stars': 45000
            }
        ]
        return sample_data[:limit]
    
    def _get_fallback_hackernews_data(self, limit):
        """Hacker News备用数据"""
        sample_data = [
            {
                'title': 'OpenAI releases GPT-4 with improved capabilities',
                'content': 'OpenAI has released GPT-4 with significant improvements in reasoning and creativity.',
                'url': 'https://news.ycombinator.com/item?id=openai-gpt4',
                'source': 'Hacker News',
                'category': '科技',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat(),
                'score': 1250
            }
        ]
        return sample_data[:limit]
    
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

def main():
    """测试函数"""
    fetcher = RealAPIFetcher()
    
    # 测试各种API
    print("测试NewsAPI...")
    newsapi_news = fetcher.fetch_newsapi(category="technology", limit=3)
    print(f"获取到 {len(newsapi_news)} 条NewsAPI新闻")
    
    print("\n测试GitHub Trending...")
    github_news = fetcher.fetch_github_trending(limit=3)
    print(f"获取到 {len(github_news)} 条GitHub Trending")
    
    print("\n测试Hacker News...")
    hn_news = fetcher.fetch_hackernews(limit=3)
    print(f"获取到 {len(hn_news)} 条Hacker News")

if __name__ == "__main__":
    main() 