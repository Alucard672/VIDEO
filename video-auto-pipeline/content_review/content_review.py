#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容审核模块
提供敏感内容检测、合规性检查等功能
"""

import re
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from config import APIConfig

class ContentReviewer:
    """内容审核器"""
    
    def __init__(self):
        self.sensitive_words = self._load_sensitive_words()
        self.platform_rules = self._load_platform_rules()
        
    def _load_sensitive_words(self) -> List[str]:
        """加载敏感词库"""
        sensitive_words = [
            # 政治敏感词
            "政治", "政府", "领导人", "国家", "政党",
            # 暴力词汇
            "暴力", "血腥", "恐怖", "死亡", "自杀",
            # 色情词汇
            "色情", "性", "裸体", "成人",
            # 违法词汇
            "毒品", "赌博", "诈骗", "非法",
            # 其他敏感词
            "歧视", "仇恨", "极端"
        ]
        return sensitive_words
    
    def _load_platform_rules(self) -> Dict:
        """加载平台规则"""
        return {
            "douyin": {
                "max_title_length": 50,
                "max_description_length": 2000,
                "forbidden_words": ["政治", "暴力", "色情"],
                "required_tags": [],
                "max_tags": 20
            },
            "bilibili": {
                "max_title_length": 80,
                "max_description_length": 4000,
                "forbidden_words": ["政治", "暴力", "色情"],
                "required_tags": [],
                "max_tags": 10
            }
        }
    
    def check_text_content(self, text: str, platform: str = "general") -> Dict:
        """检查文本内容"""
        logger.info(f"开始检查文本内容，平台: {platform}")
        
        result = {
            "passed": True,
            "issues": [],
            "suggestions": []
        }
        
        # 检查敏感词
        sensitive_issues = self._check_sensitive_words(text)
        if sensitive_issues:
            result["passed"] = False
            result["issues"].extend(sensitive_issues)
        
        # 检查长度限制
        length_issues = self._check_length_limits(text, platform)
        if length_issues:
            result["issues"].extend(length_issues)
        
        # 检查平台特定规则
        platform_issues = self._check_platform_rules(text, platform)
        if platform_issues:
            result["issues"].extend(platform_issues)
        
        # 生成建议
        result["suggestions"] = self._generate_suggestions(text, platform)
        
        logger.info(f"文本内容检查完成，通过: {result['passed']}")
        return result
    
    def _check_sensitive_words(self, text: str) -> List[str]:
        """检查敏感词"""
        issues = []
        found_words = []
        
        for word in self.sensitive_words:
            if word in text:
                found_words.append(word)
        
        if found_words:
            issues.append(f"发现敏感词: {', '.join(found_words)}")
        
        return issues
    
    def _check_length_limits(self, text: str, platform: str) -> List[str]:
        """检查长度限制"""
        issues = []
        
        if platform in self.platform_rules:
            rules = self.platform_rules[platform]
            max_length = rules.get("max_title_length", 100)
            
            if len(text) > max_length:
                issues.append(f"文本长度超过限制 ({len(text)}/{max_length})")
        
        return issues
    
    def _check_platform_rules(self, text: str, platform: str) -> List[str]:
        """检查平台特定规则"""
        issues = []
        
        if platform in self.platform_rules:
            rules = self.platform_rules[platform]
            forbidden_words = rules.get("forbidden_words", [])
            
            for word in forbidden_words:
                if word in text:
                    issues.append(f"包含平台禁止词汇: {word}")
        
        return issues
    
    def _generate_suggestions(self, text: str, platform: str) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 长度建议
        if len(text) > 100:
            suggestions.append("建议缩短文本长度，提高可读性")
        
        # 内容建议
        if len(text) < 10:
            suggestions.append("建议增加更多描述内容")
        
        # 格式建议
        if not re.search(r'[。！？]', text):
            suggestions.append("建议添加标点符号，提高可读性")
        
        return suggestions
    
    def review_video_content(self, video_info: Dict) -> Dict:
        """审核视频内容"""
        logger.info("开始审核视频内容")
        
        result = {
            "passed": True,
            "title_review": {},
            "description_review": {},
            "tags_review": {},
            "overall_issues": []
        }
        
        # 审核标题
        if "title" in video_info:
            result["title_review"] = self.check_text_content(
                video_info["title"], 
                video_info.get("platform", "general")
            )
            if not result["title_review"]["passed"]:
                result["passed"] = False
                result["overall_issues"].extend(result["title_review"]["issues"])
        
        # 审核描述
        if "description" in video_info:
            result["description_review"] = self.check_text_content(
                video_info["description"],
                video_info.get("platform", "general")
            )
            if not result["description_review"]["passed"]:
                result["passed"] = False
                result["overall_issues"].extend(result["description_review"]["issues"])
        
        # 审核标签
        if "tags" in video_info:
            result["tags_review"] = self._review_tags(
                video_info["tags"],
                video_info.get("platform", "general")
            )
            if not result["tags_review"]["passed"]:
                result["passed"] = False
                result["overall_issues"].extend(result["tags_review"]["issues"])
        
        logger.info(f"视频内容审核完成，通过: {result['passed']}")
        return result
    
    def _review_tags(self, tags: List[str], platform: str) -> Dict:
        """审核标签"""
        result = {
            "passed": True,
            "issues": [],
            "suggestions": []
        }
        
        # 检查标签数量
        if platform in self.platform_rules:
            rules = self.platform_rules[platform]
            max_tags = rules.get("max_tags", 10)
            
            if len(tags) > max_tags:
                result["passed"] = False
                result["issues"].append(f"标签数量超过限制 ({len(tags)}/{max_tags})")
        
        # 检查标签内容
        for tag in tags:
            tag_review = self.check_text_content(tag, platform)
            if not tag_review["passed"]:
                result["passed"] = False
                result["issues"].extend(tag_review["issues"])
        
        return result
    
    def review_news_content(self, news_data: Dict) -> Dict:
        """审核新闻内容"""
        logger.info("开始审核新闻内容")
        
        result = {
            "passed": True,
            "title_review": {},
            "content_review": {},
            "overall_issues": []
        }
        
        # 审核标题
        if "title" in news_data:
            result["title_review"] = self.check_text_content(news_data["title"])
            if not result["title_review"]["passed"]:
                result["passed"] = False
                result["overall_issues"].extend(result["title_review"]["issues"])
        
        # 审核内容
        if "content" in news_data:
            result["content_review"] = self.check_text_content(news_data["content"])
            if not result["content_review"]["passed"]:
                result["passed"] = False
                result["overall_issues"].extend(result["content_review"]["issues"])
        
        logger.info(f"新闻内容审核完成，通过: {result['passed']}")
        return result
    
    def batch_review_content(self, content_list: List[Dict], content_type: str = "video") -> List[Dict]:
        """批量审核内容"""
        logger.info(f"开始批量审核{content_type}内容，共{len(content_list)}条")
        
        results = []
        for i, content in enumerate(content_list):
            logger.info(f"审核第{i+1}条内容")
            
            if content_type == "video":
                result = self.review_video_content(content)
            elif content_type == "news":
                result = self.review_news_content(content)
            else:
                result = {"passed": False, "error": "不支持的内容类型"}
            
            results.append({
                "index": i,
                "content": content,
                "review_result": result
            })
        
        # 统计结果
        passed_count = sum(1 for r in results if r["review_result"]["passed"])
        logger.info(f"批量审核完成，通过: {passed_count}/{len(content_list)}")
        
        return results

def main():
    """主函数"""
    reviewer = ContentReviewer()
    
    # 测试文本审核
    test_text = "这是一个测试视频标题"
    result = reviewer.check_text_content(test_text, "douyin")
    print(f"文本审核结果: {result}")
    
    # 测试视频内容审核
    test_video = {
        "title": "测试视频标题",
        "description": "这是一个测试视频描述",
        "tags": ["测试", "视频"],
        "platform": "douyin"
    }
    result = reviewer.review_video_content(test_video)
    print(f"视频审核结果: {result}")

if __name__ == "__main__":
    main() 