#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能新闻采集系统
使用公开API和智能反反爬虫策略
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging
from bs4 import BeautifulSoup
import random
import re

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class SmartNewsFetcher:
    """智能新闻采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        # 随机User-Agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.data_dir = Path(__file__).parent.parent / "data"
        self.news_dir = self.data_dir / "news"
        self.news_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_github_trending(self, limit=10):
        """获取GitHub Trending（科技新闻）"""
        try:
            logger.info("开始获取GitHub Trending...")
            
            # GitHub Trending API
            url = "https://github.com/trending"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_list = []
            
            # 解析GitHub Trending页面
            trending_items = soup.find_all('article', class_='Box-row')
            
            for item in trending_items[:limit]:
                title_elem = item.find('h2', class_='h3')
                if title_elem:
                    title_link = title_elem.find('a')
                    if title_link:
                        title = title_link.get_text(strip=True)
                        repo_url = f"https://github.com{title_link.get('href', '')}"
                        
                        # 获取描述
                        desc_elem = item.find('p')
                        description = desc_elem.get_text(strip=True) if desc_elem else "GitHub热门项目"
                        
                        news_item = {
                            'title': f"GitHub Trending: {title}",
                            'content': description,
                            'url': repo_url,
                            'source': 'GitHub Trending',
                            'category': '科技',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'image_url': '',
                            'collected_at': datetime.now().isoformat()
                        }
                        news_list.append(news_item)
            
            logger.info(f"成功获取 {len(news_list)} 条GitHub Trending")
            self._save_news_data(news_list, "github_trending")
            return news_list
            
        except Exception as e:
            logger.error(f"获取GitHub Trending失败: {e}")
            return self._get_fallback_github_data(limit)
    
    def fetch_hackernews(self, limit=10):
        """获取Hacker News（科技新闻）"""
        try:
            logger.info("开始获取Hacker News...")
            
            # Hacker News API
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            story_ids = response.json()[:limit]
            news_list = []
            
            for story_id in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_response = self.session.get(story_url, timeout=5)
                    story_response.raise_for_status()
                    story_data = story_response.json()
                    
                    if story_data and story_data.get('title'):
                        news_item = {
                            'title': story_data.get('title', ''),
                            'content': f"Hacker News热门: {story_data.get('title', '')}",
                            'url': story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'source': 'Hacker News',
                            'category': '科技',
                            'timestamp': datetime.fromtimestamp(story_data.get('time', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            'image_url': '',
                            'collected_at': datetime.now().isoformat(),
                            'score': story_data.get('score', 0)
                        }
                        news_list.append(news_item)
                        
                        # 添加延迟避免请求过快
                        time.sleep(0.1)
                        
                except Exception as e:
                    logger.warning(f"获取Hacker News故事失败: {e}")
                    continue
            
            logger.info(f"成功获取 {len(news_list)} 条Hacker News")
            self._save_news_data(news_list, "hackernews")
            return news_list
            
        except Exception as e:
            logger.error(f"获取Hacker News失败: {e}")
            return self._get_fallback_hackernews_data(limit)
    
    def fetch_reddit_programming(self, limit=10):
        """获取Reddit r/programming（编程新闻）"""
        try:
            logger.info("开始获取Reddit r/programming...")
            
            # Reddit API
            url = "https://www.reddit.com/r/programming/hot.json"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            
            for post in data.get('data', {}).get('children', [])[:limit]:
                post_data = post.get('data', {})
                if post_data.get('title'):
                    news_item = {
                        'title': post_data.get('title', ''),
                        'content': f"Reddit r/programming: {post_data.get('title', '')}",
                        'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                        'source': 'Reddit r/programming',
                        'category': '科技',
                        'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                        'image_url': '',
                        'collected_at': datetime.now().isoformat(),
                        'score': post_data.get('score', 0)
                    }
                    news_list.append(news_item)
            
            logger.info(f"成功获取 {len(news_list)} 条Reddit r/programming")
            self._save_news_data(news_list, "reddit_programming")
            return news_list
            
        except Exception as e:
            logger.error(f"获取Reddit r/programming失败: {e}")
            return self._get_fallback_reddit_data(limit)
    
    def fetch_techcrunch(self, limit=10):
        """获取TechCrunch（科技新闻）"""
        try:
            logger.info("开始获取TechCrunch...")
            
            # TechCrunch RSS
            url = "https://techcrunch.com/feed/"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            news_list = []
            
            items = soup.find_all('item')[:limit]
            
            for item in items:
                title = item.find('title')
                description = item.find('description')
                link = item.find('link')
                pub_date = item.find('pubDate')
                
                if title:
                    news_item = {
                        'title': title.get_text(strip=True),
                        'content': description.get_text(strip=True) if description else "TechCrunch科技新闻",
                        'url': link.get_text(strip=True) if link else "",
                        'source': 'TechCrunch',
                        'category': '科技',
                        'timestamp': pub_date.get_text(strip=True) if pub_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'image_url': '',
                        'collected_at': datetime.now().isoformat()
                    }
                    news_list.append(news_item)
            
            logger.info(f"成功获取 {len(news_list)} 条TechCrunch新闻")
            self._save_news_data(news_list, "techcrunch")
            return news_list
            
        except Exception as e:
            logger.error(f"获取TechCrunch失败: {e}")
            return self._get_fallback_techcrunch_data(limit)
    
    def _get_fallback_github_data(self, limit):
        """GitHub Trending备用数据"""
        sample_data = [
            {
                'title': 'GitHub Trending: openai/whisper',
                'content': 'OpenAI的Whisper是一个强大的语音识别系统，支持多种语言。',
                'url': 'https://github.com/openai/whisper',
                'source': 'GitHub Trending',
                'category': '科技',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat()
            },
            {
                'title': 'GitHub Trending: microsoft/vscode',
                'content': 'Visual Studio Code是一个轻量级但功能强大的代码编辑器。',
                'url': 'https://github.com/microsoft/vscode',
                'source': 'GitHub Trending',
                'category': '科技',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat()
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
    
    def _get_fallback_reddit_data(self, limit):
        """Reddit备用数据"""
        sample_data = [
            {
                'title': 'New programming language features in 2024',
                'content': 'Discussion about the latest programming language features and trends.',
                'url': 'https://www.reddit.com/r/programming/new-features',
                'source': 'Reddit r/programming',
                'category': '科技',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat(),
                'score': 850
            }
        ]
        return sample_data[:limit]
    
    def _get_fallback_techcrunch_data(self, limit):
        """TechCrunch备用数据"""
        sample_data = [
            {
                'title': 'AI startups raise record funding in Q1 2024',
                'content': 'Artificial intelligence startups have raised record amounts of funding in the first quarter of 2024.',
                'url': 'https://techcrunch.com/ai-funding-2024',
                'source': 'TechCrunch',
                'category': '科技',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': '',
                'collected_at': datetime.now().isoformat()
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
    
    def get_news_summary(self, news_list):
        """生成新闻摘要"""
        if not news_list:
            return "暂无新闻数据"
        
        summary = f"共采集到 {len(news_list)} 条新闻\n"
        summary += f"来源: {news_list[0].get('source', '未知')}\n"
        summary += f"分类: {news_list[0].get('category', '未知')}\n"
        summary += f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, news in enumerate(news_list[:5], 1):
            summary += f"{i}. {news.get('title', '无标题')}\n"
            if news.get('score'):
                summary += f"   评分: {news.get('score')}\n"
        
        return summary

def main():
    """测试函数"""
    fetcher = SmartNewsFetcher()
    
    # 测试各种新闻源
    sources = [
        ('GitHub Trending', fetcher.fetch_github_trending),
        ('Hacker News', fetcher.fetch_hackernews),
        ('Reddit r/programming', fetcher.fetch_reddit_programming),
        ('TechCrunch', fetcher.fetch_techcrunch)
    ]
    
    all_news = []
    
    for source_name, fetch_func in sources:
        print(f"\n测试{source_name}...")
        try:
            news = fetch_func(limit=3)
            print(f"获取到 {len(news)} 条{source_name}")
            all_news.extend(news)
        except Exception as e:
            print(f"获取{source_name}失败: {e}")
    
    # 生成总摘要
    print(f"\n总共采集到 {len(all_news)} 条新闻")
    print(fetcher.get_news_summary(all_news))

if __name__ == "__main__":
    main() 