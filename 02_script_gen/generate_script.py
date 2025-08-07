#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本生成模块 - 基于新闻内容生成视频解说文案
"""

import json
import time
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional
import openai
from config import APIConfig

class ScriptGenerator:
    """脚本生成器"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=APIConfig.OPENAI_API_KEY)
        self.output_dir = Path("data/scripts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_script_from_news(self, news_data: Dict, style: str = "客观") -> Optional[str]:
        """基于新闻生成解说文案"""
        logger.info(f"开始为新闻生成文案: {news_data.get('title', '')}")
        
        # 构建提示词
        prompt = self._build_prompt(news_data, style)
        
        try:
            response = self.client.chat.completions.create(
                model=APIConfig.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专业的视频解说文案创作者，擅长将新闻内容转化为生动有趣的视频解说文案。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            script = response.choices[0].message.content.strip()
            logger.info("文案生成成功")
            return script
            
        except Exception as e:
            logger.error(f"文案生成失败: {e}")
            return None
    
    def _build_prompt(self, news_data: Dict, style: str) -> str:
        """构建提示词"""
        title = news_data.get('title', '')
        content = news_data.get('content', '')
        source = news_data.get('source', '')
        
        style_instructions = {
            "客观": "保持客观中立的语调，重点突出事实和数据",
            "幽默": "使用轻松幽默的语调，适当加入有趣的比喻和调侃",
            "严肃": "使用正式严肃的语调，突出事件的重大意义",
            "通俗": "使用通俗易懂的语言，避免专业术语，多用生活化比喻"
        }
        
        style_instruction = style_instructions.get(style, style_instructions["客观"])
        
        prompt = f"""
请基于以下新闻内容，生成一段适合视频解说的文案：

新闻标题：{title}
新闻内容：{content}
新闻来源：{source}

要求：
1. 文案长度控制在300-500字之间
2. 语调风格：{style_instruction}
3. 开头要有吸引人的开场白
4. 中间要包含个人观点和分析
5. 结尾要有总结和思考
6. 语言要口语化，适合朗读
7. 适当加入"个人观点"模板，如"在我看来"、"我认为"等

请直接输出文案内容，不要包含其他说明。
"""
        return prompt
    
    def add_personal_opinion_template(self, script: str) -> str:
        """添加个人观点模板"""
        templates = [
            "在我看来，",
            "我认为，",
            "从我的角度来看，",
            "不得不说，",
            "值得关注的是，",
            "值得注意的是，"
        ]
        
        # 在适当位置插入模板
        import random
        template = random.choice(templates)
        
        # 在文案中间位置插入个人观点
        lines = script.split('\n')
        if len(lines) > 2:
            insert_pos = len(lines) // 2
            lines.insert(insert_pos, f"{template}这确实是一个值得深思的问题。")
        
        return '\n'.join(lines)
    
    def control_script_length(self, script: str, target_length: int = 400) -> str:
        """控制文案长度"""
        current_length = len(script)
        
        if current_length <= target_length:
            return script
        
        # 如果太长，进行精简
        lines = script.split('\n')
        while len('\n'.join(lines)) > target_length and len(lines) > 3:
            # 删除中间的一些句子
            if len(lines) > 4:
                del lines[len(lines)//2]
        
        return '\n'.join(lines)
    
    def save_script(self, script: str, news_title: str, style: str) -> str:
        """保存文案到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in news_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # 限制标题长度
        
        filename = f"script_{timestamp}_{safe_title}_{style}.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script)
        
        logger.info(f"文案已保存到: {filepath}")
        return str(filepath)
    
    def save_script_json(self, script_data: Dict) -> str:
        """保存文案信息到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scripts_{timestamp}.json"
        filepath = Path("data") / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"文案信息已保存到: {filepath}")
        return str(filepath)
    
    def evaluate_script_quality(self, script: str) -> Dict:
        """评估文案质量"""
        quality_score = 0
        feedback = []
        
        # 长度评估
        length = len(script)
        if 300 <= length <= 500:
            quality_score += 30
            feedback.append("文案长度适中")
        elif 200 <= length <= 600:
            quality_score += 20
            feedback.append("文案长度基本合适")
        else:
            feedback.append("文案长度需要调整")
        
        # 个人观点评估
        opinion_keywords = ["我认为", "在我看来", "不得不说", "值得关注", "值得注意的是"]
        has_opinion = any(keyword in script for keyword in opinion_keywords)
        if has_opinion:
            quality_score += 25
            feedback.append("包含个人观点")
        else:
            feedback.append("缺少个人观点")
        
        # 口语化评估
        oral_keywords = ["这个", "那个", "就是", "其实", "当然", "不过"]
        has_oral = any(keyword in script for keyword in oral_keywords)
        if has_oral:
            quality_score += 25
            feedback.append("语言口语化")
        else:
            feedback.append("语言需要更口语化")
        
        # 结构评估
        has_intro = "开头" in script[:100] or any(word in script[:100] for word in ["今天", "最近", "据报道"])
        has_conclusion = "总结" in script[-100:] or any(word in script[-100:] for word in ["总之", "总的来说", "最后"])
        
        if has_intro and has_conclusion:
            quality_score += 20
            feedback.append("结构完整")
        else:
            feedback.append("结构需要完善")
        
        return {
            "score": quality_score,
            "feedback": feedback,
            "length": length,
            "has_opinion": has_opinion,
            "has_oral": has_oral,
            "has_intro": has_intro,
            "has_conclusion": has_conclusion
        }

def main():
    """主函数"""
    generator = ScriptGenerator()
    
    # 示例新闻数据
    sample_news = {
        "title": "AI技术突破：新算法大幅提升图像识别准确率",
        "content": "最新研究显示，基于深度学习的图像识别算法在准确率方面取得了重大突破，识别准确率从95%提升到98.5%。",
        "source": "科技日报"
    }
    
    # 生成不同风格的文案
    styles = ["客观", "幽默", "严肃", "通俗"]
    all_scripts = []
    
    for style in styles:
        script = generator.generate_script_from_news(sample_news, style)
        if script:
            # 添加个人观点模板
            script = generator.add_personal_opinion_template(script)
            
            # 控制长度
            script = generator.control_script_length(script)
            
            # 评估质量
            quality = generator.evaluate_script_quality(script)
            
            # 保存文案
            filepath = generator.save_script(script, sample_news['title'], style)
            
            script_data = {
                "title": sample_news['title'],
                "style": style,
                "script": script,
                "filepath": filepath,
                "quality": quality,
                "generate_time": datetime.now().isoformat()
            }
            all_scripts.append(script_data)
    
    # 保存所有文案信息
    generator.save_script_json(all_scripts)
    
    logger.info(f"文案生成完成，共生成 {len(all_scripts)} 个文案")

if __name__ == "__main__":
    main() 