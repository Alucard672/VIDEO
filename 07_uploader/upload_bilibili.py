#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站自动上传模块
"""

import time
import json
import requests
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import importlib.util
spec = importlib.util.spec_from_file_location("account_db", "06_account_manager/account_db.py")
account_db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(account_db)
AccountDatabase = account_db.AccountDatabase
from config import UploadConfig

class BilibiliUploader:
    """B站上传器"""
    
    def __init__(self):
        self.db = AccountDatabase()
        self.driver = None
        self.wait_timeout = 30
        
        # 上传配置
        self.upload_interval = UploadConfig.BILIBILI_UPLOAD_INTERVAL
        self.max_daily_uploads = UploadConfig.MAX_DAILY_UPLOADS
    
    def setup_driver(self, headless: bool = False) -> bool:
        """设置WebDriver"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("B站上传器WebDriver设置成功")
            return True
            
        except Exception as e:
            logger.error(f"B站上传器WebDriver设置失败: {e}")
            return False
    
    def close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("B站上传器WebDriver已关闭")
    
    def login_account(self, account_id: int) -> bool:
        """登录账号"""
        logger.info(f"开始登录B站账号: {account_id}")
        
        try:
            # 获取账号信息
            account_data = self.db.get_account(account_id)
            if not account_data:
                logger.error(f"账号不存在: {account_id}")
                return False
            
            # 访问B站创作中心
            self.driver.get("https://member.bilibili.com/platform/home")
            time.sleep(3)
            
            # 检查是否已登录
            if self._check_login_status():
                logger.info("B站账号已登录")
                return True
            
            # 尝试使用Cookie登录
            if account_data.get('cookies'):
                if self._load_cookies(account_data):
                    if self._check_login_status():
                        logger.info("Cookie登录成功")
                        return True
            
            # 手动登录
            logger.info("需要手动登录，请在浏览器中完成登录")
            self.driver.get("https://www.bilibili.com")
            
            # 等待用户手动登录
            while not self._check_login_status():
                time.sleep(2)
                logger.info("等待用户登录...")
            
            # 保存Cookie
            self._save_cookies(account_id)
            
            logger.info("B站账号登录成功")
            return True
            
        except Exception as e:
            logger.error(f"B站账号登录失败: {e}")
            return False
    
    def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查是否存在用户头像或用户名
            user_avatar = self.driver.find_elements(By.CSS_SELECTOR, ".header-avatar")
            if user_avatar:
                return True
            
            # 检查是否存在登录按钮
            login_btn = self.driver.find_elements(By.CSS_SELECTOR, ".header-login-entry")
            if not login_btn:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def _load_cookies(self, account_data: Dict) -> bool:
        """加载Cookie"""
        try:
            cookies = account_data.get('cookies')
            if not cookies:
                return False
            
            # 解析Cookie
            if isinstance(cookies, str):
                cookies = json.loads(cookies)
            
            # 访问B站
            self.driver.get("https://www.bilibili.com")
            time.sleep(2)
            
            # 添加Cookie
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加Cookie失败: {e}")
            
            # 刷新页面
            self.driver.refresh()
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return False
    
    def _save_cookies(self, account_id: int) -> bool:
        """保存Cookie"""
        try:
            cookies = self.driver.get_cookies()
            
            if cookies:
                # 更新数据库中的Cookie
                success = self.db.update_account(account_id, cookies=json.dumps(cookies))
                
                if success:
                    logger.info(f"Cookie保存成功: {account_id}")
                    return True
                else:
                    logger.error(f"Cookie保存失败: {account_id}")
                    return False
            else:
                logger.warning("没有获取到Cookie")
                return False
                
        except Exception as e:
            logger.error(f"保存Cookie异常: {e}")
            return False
    
    def upload_video(self, account_id: int, video_path: str, title: str, 
                    description: str = "", tags: List[str] = None, 
                    cover_path: str = None, category: str = "科技") -> bool:
        """上传视频"""
        logger.info(f"开始上传视频: {video_path}")
        
        try:
            # 登录账号
            if not self.login_account(account_id):
                return False
            
            # 访问创作中心
            self.driver.get("https://member.bilibili.com/platform/post")
            time.sleep(3)
            
            # 点击发布视频
            publish_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".publish-btn"))
            )
            publish_btn.click()
            
            # 上传视频文件
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(video_path).absolute()))
            
            # 等待视频上传完成
            logger.info("等待视频上传...")
            WebDriverWait(self.driver, 300).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".upload-progress"))
            )
            
            # 填写标题
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='标题']"))
            )
            title_input.clear()
            title_input.send_keys(title)
            
            # 填写简介
            if description:
                desc_input = self.driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='简介']")
                desc_input.clear()
                desc_input.send_keys(description)
            
            # 选择分区
            category_btn = self.driver.find_element(By.CSS_SELECTOR, ".category-selector")
            category_btn.click()
            
            # 选择科技分区
            tech_category = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{category}')]"))
            )
            tech_category.click()
            
            # 添加标签
            if tags:
                for tag in tags:
                    tag_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='标签']")
                    tag_input.clear()
                    tag_input.send_keys(tag)
                    tag_input.send_keys("\n")
                    time.sleep(1)
            
            # 上传封面（如果有）
            if cover_path:
                cover_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='image']")
                cover_input.send_keys(str(Path(cover_path).absolute()))
                time.sleep(2)
            
            # 发布视频
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            submit_btn.click()
            
            # 等待发布完成
            logger.info("等待视频发布...")
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".publish-success"))
            )
            
            logger.info("视频上传成功")
            return True
            
        except Exception as e:
            logger.error(f"视频上传失败: {e}")
            return False
    
    def batch_upload_videos(self, upload_data_list: List[Dict]) -> List[Dict]:
        """批量上传视频"""
        logger.info(f"开始批量上传视频，共 {len(upload_data_list)} 个")
        
        results = []
        
        for i, upload_data in enumerate(upload_data_list):
            logger.info(f"上传第 {i+1}/{len(upload_data_list)} 个视频")
            
            account_id = upload_data.get('account_id')
            video_path = upload_data.get('video_path', '')
            title = upload_data.get('title', '')
            description = upload_data.get('description', '')
            tags = upload_data.get('tags', [])
            cover_path = upload_data.get('cover_path', '')
            category = upload_data.get('category', '科技')
            
            if not all([account_id, video_path, title]):
                logger.warning(f"上传数据不完整，跳过: {upload_data}")
                continue
            
            # 上传视频
            success = self.upload_video(
                account_id, video_path, title, description, tags, cover_path, category
            )
            
            result = {
                "upload_id": i,
                "account_id": account_id,
                "video_path": video_path,
                "title": title,
                "status": "success" if success else "failed",
                "upload_time": time.time()
            }
            
            results.append(result)
            
            # 添加延迟避免频繁上传
            time.sleep(self.upload_interval)
        
        success_count = len([r for r in results if r['status'] == 'success'])
        logger.info(f"批量上传完成，成功: {success_count}/{len(upload_data_list)}")
        
        return results
    
    def get_upload_stats(self, account_id: int) -> Dict:
        """获取上传统计"""
        try:
            # 这里可以添加获取上传统计的逻辑
            # 比如今日上传数量、总上传数量等
            
            stats = {
                "account_id": account_id,
                "today_uploads": 0,
                "total_uploads": 0,
                "last_upload_time": None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取上传统计失败: {e}")
            return {}

def main():
    """主函数"""
    uploader = BilibiliUploader()
    
    # 示例：上传视频
    upload_data = [
        {
            "account_id": 1,
            "video_path": "data/edited_videos/sample_video.mp4",
            "title": "AI技术突破：新算法大幅提升准确率",
            "description": "最新研究显示，基于深度学习的图像识别算法在准确率方面取得了重大突破。",
            "tags": ["科技", "AI", "人工智能"],
            "cover_path": "data/thumbnails/sample_thumbnail.png",
            "category": "科技"
        }
    ]
    
    # 批量上传
    results = uploader.batch_upload_videos(upload_data)
    
    logger.info(f"B站上传完成，共上传 {len(results)} 个视频")

if __name__ == "__main__":
    main() 