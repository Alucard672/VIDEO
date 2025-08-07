#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统状态检查脚本
"""

import requests
import json
from datetime import datetime

def check_news_api():
    """检查新闻采集API"""
    print("=== 检查新闻采集API ===")
    try:
        response = requests.post(
            'http://localhost:8081/api/fetch_news',
            json={'category': '热点', 'count': 2, 'source': 'sina'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 新闻采集API正常")
            print(f"   采集数量: {data.get('count', 0)}")
            print(f"   数据源: {data.get('source', '')}")
            print(f"   成功状态: {data.get('success', False)}")
            return True
        else:
            print(f"❌ 新闻采集API错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 新闻采集API连接失败: {e}")
        return False

def check_video_api():
    """检查视频采集API"""
    print("\n=== 检查视频采集API ===")
    try:
        response = requests.post(
            'http://localhost:8081/api/fetch_videos',
            json={'platform': 'bilibili', 'count': 2, 'type': '热门'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 视频采集API正常")
            print(f"   采集数量: {data.get('count', 0)}")
            print(f"   平台: {data.get('platform', '')}")
            print(f"   成功状态: {data.get('success', False)}")
            return True
        else:
            print(f"❌ 视频采集API错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 视频采集API连接失败: {e}")
        return False

def check_web_interface():
    """检查Web界面"""
    print("\n=== 检查Web界面 ===")
    try:
        response = requests.get('http://localhost:8081/', timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Web界面正常")
            print(f"   访问地址: http://localhost:8081")
            return True
        else:
            print(f"❌ Web界面错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Web界面连接失败: {e}")
        return False

def main():
    """主函数"""
    print("视频自动化系统状态检查")
    print("=" * 50)
    
    # 检查各项功能
    news_ok = check_news_api()
    video_ok = check_video_api()
    web_ok = check_web_interface()
    
    print("\n" + "=" * 50)
    print("检查结果汇总:")
    print(f"新闻采集: {'✅ 正常' if news_ok else '❌ 异常'}")
    print(f"视频采集: {'✅ 正常' if video_ok else '❌ 异常'}")
    print(f"Web界面: {'✅ 正常' if web_ok else '❌ 异常'}")
    
    if all([news_ok, video_ok, web_ok]):
        print("\n🎉 系统运行正常！")
        print("请访问: http://localhost:8081")
    else:
        print("\n⚠️  系统存在问题，请检查上述错误信息")

if __name__ == "__main__":
    main() 