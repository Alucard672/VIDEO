#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动登录与Cookie加载模块
"""

import time
import json
from pathlib import Path
from loguru import logger
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from account_db import AccountDatabase

class LoginHandler:
    """登录处理器"""
    
    def __init__(self):
        self.db = AccountDatabase()
        self.driver = None
        self.wait_timeout = 10
        
    def setup_driver(self, headless: bool = True) -> bool:
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
            self.driver.implicitly_wait(5)
            
            logger.info("WebDriver设置成功")
            return True
            
        except Exception as e:
            logger.error(f"WebDriver设置失败: {e}")
            return False
    
    def close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver已关闭")
    
    def load_cookies(self, account_data: Dict) -> bool:
        """加载Cookie"""
        logger.info(f"开始加载Cookie: {account_data.get('username', '')}")
        
        try:
            cookies = account_data.get('cookies')
            if not cookies:
                logger.warning("账号没有保存的Cookie")
                return False
            
            # 解析Cookie
            if isinstance(cookies, str):
                cookies = json.loads(cookies)
            
            # 访问目标网站
            platform = account_data.get('platform', '')
            if platform == 'douyin':
                self.driver.get("https://www.douyin.com")
            elif platform == 'bilibili':
                self.driver.get("https://www.bilibili.com")
            else:
                logger.error(f"不支持的平台: {platform}")
                return False
            
            # 添加Cookie
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加Cookie失败: {e}")
            
            # 刷新页面
            self.driver.refresh()
            time.sleep(2)
            
            # 检查登录状态
            if self.check_login_status(platform):
                logger.info("Cookie加载成功，已登录")
                return True
            else:
                logger.warning("Cookie加载失败，未登录")
                return False
                
        except Exception as e:
            logger.error(f"Cookie加载异常: {e}")
            return False
    
    def check_login_status(self, platform: str) -> bool:
        """检查登录状态"""
        try:
            if platform == 'douyin':
                # 检查抖音登录状态
                try:
                    # 查找用户头像或用户名元素
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-avatar']"))
                    )
                    return True
                except:
                    return False
                    
            elif platform == 'bilibili':
                # 检查B站登录状态
                try:
                    # 查找用户头像或用户名元素
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".header-avatar"))
                    )
                    return True
                except:
                    return False
                    
            else:
                logger.warning(f"不支持的平台: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def manual_login_douyin(self, username: str, password: str) -> bool:
        """手动登录抖音"""
        logger.info("开始手动登录抖音")
        
        try:
            self.driver.get("https://www.douyin.com")
            time.sleep(2)
            
            # 点击登录按钮
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-e2e='login-button']"))
            )
            login_btn.click()
            
            # 切换到密码登录
            password_login = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '密码登录')]"))
            )
            password_login.click()
            
            # 输入用户名
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='手机号']"))
            )
            username_input.clear()
            username_input.send_keys(username)
            
            # 输入密码
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='密码']")
            password_input.clear()
            password_input.send_keys(password)
            
            # 点击登录
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            # 等待登录完成
            time.sleep(5)
            
            # 检查登录状态
            if self.check_login_status('douyin'):
                logger.info("抖音手动登录成功")
                return True
            else:
                logger.error("抖音手动登录失败")
                return False
                
        except Exception as e:
            logger.error(f"抖音手动登录异常: {e}")
            return False
    
    def manual_login_bilibili(self, username: str, password: str) -> bool:
        """手动登录B站"""
        logger.info("开始手动登录B站")
        
        try:
            self.driver.get("https://www.bilibili.com")
            time.sleep(2)
            
            # 点击登录按钮
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".header-login-entry"))
            )
            login_btn.click()
            
            # 切换到密码登录
            password_login = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '密码登录')]"))
            )
            password_login.click()
            
            # 输入用户名
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']"))
            )
            username_input.clear()
            username_input.send_keys(username)
            
            # 输入密码
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='密码']")
            password_input.clear()
            password_input.send_keys(password)
            
            # 点击登录
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            # 等待登录完成
            time.sleep(5)
            
            # 检查登录状态
            if self.check_login_status('bilibili'):
                logger.info("B站手动登录成功")
                return True
            else:
                logger.error("B站手动登录失败")
                return False
                
        except Exception as e:
            logger.error(f"B站手动登录异常: {e}")
            return False
    
    def save_cookies(self, account_id: int) -> bool:
        """保存Cookie"""
        logger.info(f"开始保存Cookie: {account_id}")
        
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
    
    def login_account(self, account_id: int, manual_login: bool = False) -> bool:
        """登录账号"""
        logger.info(f"开始登录账号: {account_id}")
        
        try:
            # 获取账号信息
            account_data = self.db.get_account(account_id)
            if not account_data:
                logger.error(f"账号不存在: {account_id}")
                return False
            
            # 设置WebDriver
            if not self.setup_driver():
                return False
            
            try:
                # 尝试使用Cookie登录
                if not manual_login and account_data.get('cookies'):
                    if self.load_cookies(account_data):
                        # 记录登录日志
                        self.db.add_login_log(account_id, "success", "127.0.0.1", "selenium")
                        return True
                
                # 手动登录
                if manual_login:
                    platform = account_data.get('platform', '')
                    username = account_data.get('username', '')
                    password = account_data.get('password', '')
                    
                    if platform == 'douyin':
                        success = self.manual_login_douyin(username, password)
                    elif platform == 'bilibili':
                        success = self.manual_login_bilibili(username, password)
                    else:
                        logger.error(f"不支持的平台: {platform}")
                        return False
                    
                    if success:
                        # 保存Cookie
                        self.save_cookies(account_id)
                        # 记录登录日志
                        self.db.add_login_log(account_id, "success", "127.0.0.1", "selenium")
                        return True
                    else:
                        # 记录登录日志
                        self.db.add_login_log(account_id, "failed", "127.0.0.1", "selenium")
                        return False
                
                logger.warning("Cookie登录失败，需要手动登录")
                return False
                
            finally:
                self.close_driver()
                
        except Exception as e:
            logger.error(f"登录账号异常: {e}")
            return False
    
    def batch_login_accounts(self, account_ids: List[int], manual_login: bool = False) -> List[Dict]:
        """批量登录账号"""
        logger.info(f"开始批量登录账号，共 {len(account_ids)} 个")
        
        results = []
        
        for account_id in account_ids:
            logger.info(f"登录第 {len(results) + 1}/{len(account_ids)} 个账号")
            
            success = self.login_account(account_id, manual_login)
            
            result = {
                "account_id": account_id,
                "status": "success" if success else "failed",
                "login_time": time.time()
            }
            
            results.append(result)
            
            # 添加延迟避免频繁登录
            time.sleep(2)
        
        success_count = len([r for r in results if r['status'] == 'success'])
        logger.info(f"批量登录完成，成功: {success_count}/{len(account_ids)}")
        
        return results

def main():
    """主函数"""
    handler = LoginHandler()
    
    # 示例：登录账号
    account_ids = [1]  # 假设账号ID为1
    
    results = handler.batch_login_accounts(account_ids, manual_login=False)
    
    logger.info(f"登录处理完成，共处理 {len(results)} 个账号")

if __name__ == "__main__":
    main() 