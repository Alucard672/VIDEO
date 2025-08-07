#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号状态监控与异常提醒模块
"""

import time
import json
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from account_db import AccountDatabase
from login_handler import LoginHandler

class AccountMonitor:
    """账号监控器"""
    
    def __init__(self):
        self.db = AccountDatabase()
        self.login_handler = LoginHandler()
        
        # 监控配置
        self.monitor_interval = 3600  # 监控间隔（秒）
        self.max_failed_logins = 3    # 最大失败登录次数
        self.max_inactive_days = 7    # 最大不活跃天数
        
        # 通知配置
        self.email_config = {
            "smtp_server": "smtp.qq.com",
            "smtp_port": 587,
            "sender_email": "your_email@qq.com",
            "sender_password": "your_password",
            "recipient_email": "admin@example.com"
        }
        
        # 微信通知配置（需要企业微信或微信公众号）
        self.wechat_config = {
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
        }
    
    def check_account_status(self, account_id: int) -> Dict:
        """检查单个账号状态"""
        logger.info(f"检查账号状态: {account_id}")
        
        try:
            account_data = self.db.get_account(account_id)
            if not account_data:
                return {"account_id": account_id, "status": "not_found"}
            
            status_info = {
                "account_id": account_id,
                "platform": account_data.get('platform', ''),
                "username": account_data.get('username', ''),
                "status": "unknown",
                "last_login": account_data.get('last_login'),
                "login_count": account_data.get('login_count', 0),
                "issues": []
            }
            
            # 检查登录状态
            if self._check_login_status(account_data):
                status_info["status"] = "active"
            else:
                status_info["status"] = "inactive"
                status_info["issues"].append("登录状态异常")
            
            # 检查登录失败次数
            failed_logins = self._get_recent_failed_logins(account_id)
            if len(failed_logins) >= self.max_failed_logins:
                status_info["issues"].append(f"登录失败次数过多: {len(failed_logins)}")
            
            # 检查不活跃时间
            if self._check_inactive_period(account_data):
                status_info["issues"].append("账号长期未登录")
            
            # 检查Cookie有效性
            if not self._check_cookie_validity(account_data):
                status_info["issues"].append("Cookie已失效")
            
            logger.info(f"账号状态检查完成: {status_info['status']}")
            return status_info
            
        except Exception as e:
            logger.error(f"检查账号状态失败: {e}")
            return {"account_id": account_id, "status": "error", "error": str(e)}
    
    def _check_login_status(self, account_data: Dict) -> bool:
        """检查登录状态"""
        try:
            platform = account_data.get('platform', '')
            
            # 使用登录处理器检查状态
            if platform in ['douyin', 'bilibili']:
                # 这里可以调用登录处理器的检查方法
                # 为了简化，这里使用模拟检查
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def _get_recent_failed_logins(self, account_id: int, days: int = 7) -> List[Dict]:
        """获取最近的失败登录记录"""
        try:
            logs = self.db.get_login_logs(account_id, limit=100)
            
            # 过滤最近几天的失败记录
            cutoff_time = datetime.now() - timedelta(days=days)
            failed_logs = []
            
            for log in logs:
                if log.get('status') == 'failed':
                    log_time = datetime.fromisoformat(log.get('login_time', ''))
                    if log_time > cutoff_time:
                        failed_logs.append(log)
            
            return failed_logs
            
        except Exception as e:
            logger.error(f"获取失败登录记录失败: {e}")
            return []
    
    def _check_inactive_period(self, account_data: Dict) -> bool:
        """检查不活跃时间"""
        try:
            last_login = account_data.get('last_login')
            if not last_login:
                return True
            
            # 解析最后登录时间
            if isinstance(last_login, str):
                last_login_time = datetime.fromisoformat(last_login)
            else:
                last_login_time = last_login
            
            # 检查是否超过最大不活跃天数
            cutoff_time = datetime.now() - timedelta(days=self.max_inactive_days)
            return last_login_time < cutoff_time
            
        except Exception as e:
            logger.error(f"检查不活跃时间失败: {e}")
            return True
    
    def _check_cookie_validity(self, account_data: Dict) -> bool:
        """检查Cookie有效性"""
        try:
            cookies = account_data.get('cookies')
            if not cookies:
                return False
            
            # 这里可以添加Cookie有效性检查逻辑
            # 为了简化，这里返回True
            return True
            
        except Exception as e:
            logger.error(f"检查Cookie有效性失败: {e}")
            return False
    
    def batch_check_accounts(self, account_ids: List[int] = None) -> List[Dict]:
        """批量检查账号状态"""
        logger.info("开始批量检查账号状态")
        
        if account_ids is None:
            # 获取所有活跃账号
            accounts = self.db.get_active_accounts()
            account_ids = [account['id'] for account in accounts]
        
        results = []
        
        for account_id in account_ids:
            status_info = self.check_account_status(account_id)
            results.append(status_info)
            
            # 添加延迟避免频繁检查
            time.sleep(1)
        
        logger.info(f"批量检查完成，共检查 {len(results)} 个账号")
        return results
    
    def send_email_notification(self, subject: str, content: str) -> bool:
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['sender_email'], self.email_config['recipient_email'], text)
            server.quit()
            
            logger.info("邮件通知发送成功")
            return True
            
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
            return False
    
    def send_wechat_notification(self, content: str) -> bool:
        """发送微信通知"""
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            response = requests.post(
                self.wechat_config['webhook_url'],
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("微信通知发送成功")
                return True
            else:
                logger.error(f"微信通知发送失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"微信通知发送异常: {e}")
            return False
    
    def generate_notification_content(self, status_results: List[Dict]) -> str:
        """生成通知内容"""
        content = "账号状态监控报告\n"
        content += f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"检查账号数: {len(status_results)}\n\n"
        
        # 统计状态
        status_counts = {}
        issue_accounts = []
        
        for result in status_results:
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if result.get('issues'):
                issue_accounts.append(result)
        
        # 状态统计
        content += "状态统计:\n"
        for status, count in status_counts.items():
            content += f"- {status}: {count}个\n"
        
        # 问题账号
        if issue_accounts:
            content += "\n问题账号:\n"
            for account in issue_accounts:
                content += f"- {account.get('platform', '')} - {account.get('username', '')}\n"
                for issue in account.get('issues', []):
                    content += f"  * {issue}\n"
        
        return content
    
    def monitor_and_notify(self, account_ids: List[int] = None) -> bool:
        """监控并发送通知"""
        logger.info("开始监控并发送通知")
        
        try:
            # 检查账号状态
            status_results = self.batch_check_accounts(account_ids)
            
            # 生成通知内容
            content = self.generate_notification_content(status_results)
            
            # 检查是否有问题账号
            has_issues = any(result.get('issues') for result in status_results)
            
            if has_issues:
                # 发送邮件通知
                subject = "账号状态异常提醒"
                self.send_email_notification(subject, content)
                
                # 发送微信通知
                self.send_wechat_notification(content)
                
                logger.info("异常通知已发送")
                return True
            else:
                logger.info("所有账号状态正常")
                return False
                
        except Exception as e:
            logger.error(f"监控通知失败: {e}")
            return False
    
    def start_monitoring(self, interval: int = None):
        """开始持续监控"""
        if interval is None:
            interval = self.monitor_interval
        
        logger.info(f"开始持续监控，间隔: {interval}秒")
        
        try:
            while True:
                logger.info("执行监控检查...")
                
                # 执行监控
                self.monitor_and_notify()
                
                # 等待下次检查
                logger.info(f"等待 {interval} 秒后进行下次检查...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("监控已停止")
        except Exception as e:
            logger.error(f"监控异常: {e}")

def main():
    """主函数"""
    monitor = AccountMonitor()
    
    # 示例：检查账号状态
    account_ids = [1]  # 假设账号ID为1
    
    # 批量检查
    results = monitor.batch_check_accounts(account_ids)
    
    # 生成报告
    content = monitor.generate_notification_content(results)
    logger.info(f"监控报告:\n{content}")
    
    # 发送通知
    monitor.monitor_and_notify(account_ids)
    
    logger.info("账号监控完成")

if __name__ == "__main__":
    main() 