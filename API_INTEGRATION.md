# API集成指南

## 📋 概述

本系统支持多种真实API集成，包括新闻采集、视频采集等。以下是详细的配置和使用说明。

## 🔧 API配置

### 1. 新闻API配置

#### NewsAPI (推荐)
- 注册地址：https://newsapi.org/
- 免费额度：每天1000次请求
- 配置方法：
```bash
# 在 config/.env 文件中添加
NEWS_API_KEY=your_api_key_here
```

#### 网易新闻API
- 无需API密钥
- 直接使用系统内置的采集器

#### 新浪新闻API
- 无需API密钥
- 直接使用系统内置的采集器

### 2. 视频API配置

#### YouTube Data API
- 注册地址：https://console.developers.google.com/
- 免费额度：每天10000次请求
- 配置方法：
```bash
# 在 config/.env 文件中添加
YOUTUBE_API_KEY=your_api_key_here
```

#### B站API
- 无需API密钥
- 使用公开API接口

## 🚀 使用方法

### 1. 配置API密钥

```bash
# 进入配置目录
cd video-auto-pipeline/config

# 运行配置脚本
python api_config.py
```

### 2. 测试API连接

```bash
# 测试新闻API
curl -X POST -H "Content-Type: application/json" \
  -d '{"category":"technology","count":5}' \
  http://localhost:8080/api/real_news

# 测试系统健康检查
curl http://localhost:8080/api/system_health
```

### 3. Web界面使用

1. 启动Web服务器
```bash
python simple_web.py
```

2. 访问素材采集页面
   - 打开 http://localhost:8080/fetch
   - 选择新闻来源
   - 点击"开始采集新闻"

## 📊 API状态监控

系统会自动检测API配置状态：

- ✅ 已配置：API密钥已设置，可以正常使用
- ❌ 未配置：使用模拟数据，功能受限
- ⚠️ 错误：API请求失败，使用备用方案

## 🔄 真实数据 vs 模拟数据

### 真实数据特点：
- 实时更新
- 内容丰富
- 需要API密钥
- 可能有请求限制

### 模拟数据特点：
- 无需配置
- 响应快速
- 数据稳定
- 适合演示

## 🛠️ 自定义API集成

### 添加新的新闻源

1. 在 `01_content_fetch/fetch_news.py` 中添加新方法
2. 在 `simple_web.py` 中添加对应的API路由
3. 在 `config/api_config.py` 中添加配置项

### 添加新的视频源

1. 在 `01_content_fetch/fetch_videos.py` 中添加新方法
2. 在 `simple_web.py` 中添加对应的API路由
3. 在 `config/api_config.py` 中添加配置项

## 📝 示例代码

### 新闻API集成示例

```python
import requests
from config.api_config import api_config

def fetch_news_from_api(category, count=10):
    api_key = api_config.get('news_api_key')
    if not api_key:
        return []
    
    url = api_config.get('news_api_url')
    params = {
        'apiKey': api_key,
        'category': category,
        'pageSize': count,
        'language': 'zh'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        news_list = []
        for article in data.get('articles', []):
            news_item = {
                'title': article.get('title', ''),
                'content': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', ''),
                'timestamp': article.get('publishedAt', ''),
                'image_url': article.get('urlToImage', ''),
                'collected_at': datetime.now().isoformat()
            }
            news_list.append(news_item)
        
        return news_list
    except Exception as e:
        print(f"API请求失败: {e}")
        return []
```

### 视频API集成示例

```python
import requests
from config.api_config import api_config

def fetch_youtube_videos(query, count=10):
    api_key = api_config.get('youtube_api_key')
    if not api_key:
        return []
    
    url = api_config.get('youtube_api_url') + '/search'
    params = {
        'key': api_key,
        'part': 'snippet',
        'q': query,
        'maxResults': count,
        'type': 'video',
        'order': 'viewCount'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        videos_list = []
        for item in data.get('items', []):
            snippet = item.get('snippet', {})
            video_info = {
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'url': f"https://youtube.com/watch?v={item.get('id', {}).get('videoId', '')}",
                'platform': 'youtube',
                'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'published_at': snippet.get('publishedAt', ''),
                'collected_at': datetime.now().isoformat()
            }
            videos_list.append(video_info)
        
        return videos_list
    except Exception as e:
        print(f"YouTube API请求失败: {e}")
        return []
```

## 🔒 安全注意事项

1. **API密钥保护**
   - 不要将API密钥提交到版本控制系统
   - 使用环境变量或配置文件存储密钥
   - 定期轮换API密钥

2. **请求限制**
   - 遵守API提供商的请求限制
   - 实现请求缓存机制
   - 添加错误重试机制

3. **数据隐私**
   - 只采集公开数据
   - 遵守相关法律法规
   - 保护用户隐私

## 📞 技术支持

如果遇到API集成问题，请检查：

1. API密钥是否正确配置
2. 网络连接是否正常
3. API配额是否充足
4. 请求格式是否符合要求

## 🔄 更新日志

- v1.0.0: 基础API集成
- v1.1.0: 添加NewsAPI支持
- v1.2.0: 添加YouTube API支持
- v1.3.0: 添加系统健康检查 