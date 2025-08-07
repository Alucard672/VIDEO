#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的新闻采集模块
不依赖外部包，使用内置库实现
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging
import random

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
        获取网易新闻（模拟数据）
        
        Args:
            category: 新闻分类
            limit: 获取数量限制
        
        Returns:
            list: 新闻列表
        """
        try:
            logger.info(f"开始获取网易新闻 - 分类: {category}")
            
            # 使用模拟数据
            sample_news = [
                {
                    'title': f'{category}新闻：人工智能技术发展迅速，ChatGPT引领AI革命',
                    'content': '随着人工智能技术的快速发展，ChatGPT等大语言模型正在改变我们的工作和生活方式。专家表示，AI技术将在未来几年内带来更多创新。',
                    'url': 'https://news.163.com/ai/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：新能源汽车市场持续增长，充电基础设施建设加快',
                    'content': '新能源汽车市场继续保持强劲增长势头，各大车企纷纷推出新车型。同时，充电基础设施建设也在加快推进，为新能源汽车普及提供保障。',
                    'url': 'https://news.163.com/auto/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：5G技术应用广泛，智慧城市建设加速推进',
                    'content': '5G技术在各行各业的应用越来越广泛，从工业互联网到智慧城市，5G正在成为数字化转型的重要基础设施。',
                    'url': 'https://news.163.com/tech/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：数字经济蓬勃发展，数字化转型成为企业必选项',
                    'content': '在疫情推动下，数字经济快速发展，越来越多的企业开始数字化转型。专家认为，数字化将成为企业竞争力的重要指标。',
                    'url': 'https://news.163.com/economy/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：绿色能源发展迅速，可再生能源占比不断提升',
                    'content': '随着环保意识的提升，绿色能源发展迅速。太阳能、风能等可再生能源的占比不断提升，为可持续发展贡献力量。',
                    'url': 'https://news.163.com/environment/',
                    'source': '网易新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            # 根据limit返回指定数量的新闻
            news_list = sample_news[:limit]
            
            logger.info(f"成功获取 {len(news_list)} 条网易新闻")
            
            # 保存新闻数据
            self._save_news_data(news_list, f"netease_{category}")
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取网易新闻失败: {e}")
            return []
    
    def fetch_sina_news(self, category="热点", limit=10):
        """
        获取新浪新闻（模拟数据）
        
        Args:
            category: 新闻分类
            limit: 获取数量限制
        
        Returns:
            list: 新闻列表
        """
        try:
            logger.info(f"开始获取新浪新闻 - 分类: {category}")
            
            # 使用模拟数据
            sample_news = [
                {
                    'title': f'{category}新闻：科技创新推动产业升级，新业态不断涌现',
                    'content': '科技创新正在推动传统产业升级改造，新业态、新模式不断涌现。专家表示，创新是推动经济发展的核心动力。',
                    'url': 'https://news.sina.com.cn/tech/',
                    'source': '新浪新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：教育数字化转型加速，在线教育迎来新机遇',
                    'content': '疫情推动了教育数字化转型，在线教育平台快速发展。专家认为，线上线下融合将成为未来教育的重要趋势。',
                    'url': 'https://news.sina.com.cn/education/',
                    'source': '新浪新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：医疗健康产业快速发展，智慧医疗应用广泛',
                    'content': '医疗健康产业在技术创新推动下快速发展，智慧医疗、远程诊疗等新应用不断涌现，为患者提供更好的医疗服务。',
                    'url': 'https://news.sina.com.cn/health/',
                    'source': '新浪新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：文化产业发展迅速，数字文化成为新亮点',
                    'content': '文化产业在数字化浪潮下快速发展，数字文化、网络文学等新业态成为产业发展的重要亮点。',
                    'url': 'https://news.sina.com.cn/culture/',
                    'source': '新浪新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                },
                {
                    'title': f'{category}新闻：体育产业蓬勃发展，全民健身意识提升',
                    'content': '体育产业在政策支持下蓬勃发展，全民健身意识不断提升。体育消费成为新的经济增长点。',
                    'url': 'https://news.sina.com.cn/sports/',
                    'source': '新浪新闻',
                    'category': category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_url': '',
                    'collected_at': datetime.now().isoformat()
                }
            ]
            
            # 根据limit返回指定数量的新闻
            news_list = sample_news[:limit]
            
            logger.info(f"成功获取 {len(news_list)} 条新浪新闻")
            
            # 保存新闻数据
            self._save_news_data(news_list, f"sina_{category}")
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取新浪新闻失败: {e}")
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
        """生成新闻摘要"""
        if not news_list:
            return "暂无新闻数据"
        
        summary = f"共采集到 {len(news_list)} 条新闻\n"
        summary += f"来源: {news_list[0].get('source', '未知')}\n"
        summary += f"分类: {news_list[0].get('category', '未知')}\n"
        summary += f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, news in enumerate(news_list[:5], 1):
            summary += f"{i}. {news.get('title', '无标题')}\n"
        
        return summary

def main():
    """测试函数"""
    fetcher = NewsFetcher()
    
    # 测试网易新闻采集
    print("测试网易新闻采集...")
    netease_news = fetcher.fetch_netease_news(category="热点", limit=3)
    print(f"获取到 {len(netease_news)} 条网易新闻")
    
    # 测试新浪新闻采集
    print("\n测试新浪新闻采集...")
    sina_news = fetcher.fetch_sina_news(category="科技", limit=3)
    print(f"获取到 {len(sina_news)} 条新浪新闻")
    
    # 生成摘要
    print("\n新闻摘要:")
    print(fetcher.get_news_summary(netease_news + sina_news))

if __name__ == "__main__":
    main() 