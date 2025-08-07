#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频封面生成模块
"""

import requests
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from typing import Dict, List, Optional
from config import APIConfig

class ThumbnailGenerator:
    """封面生成器"""
    
    def __init__(self):
        self.output_dir = Path("data/thumbnails")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 封面模板配置
        self.templates = {
            "default": {
                "width": 1920,
                "height": 1080,
                "background_color": (0, 0, 0),
                "text_color": (255, 255, 255),
                "font_size": 60
            },
            "modern": {
                "width": 1920,
                "height": 1080,
                "background_color": (25, 25, 35),
                "text_color": (255, 255, 255),
                "font_size": 70
            },
            "vintage": {
                "width": 1920,
                "height": 1080,
                "background_color": (139, 69, 19),
                "text_color": (255, 215, 0),
                "font_size": 65
            }
        }
    
    def generate_dalle_background(self, prompt: str, style: str = "modern") -> Optional[str]:
        """使用DALL-E生成背景图片"""
        logger.info(f"开始使用DALL-E生成背景: {prompt}")
        
        if not APIConfig.OPENAI_API_KEY:
            logger.warning("OpenAI API密钥未配置，使用默认背景")
            return self._generate_default_background()
        
        try:
            import openai
            client = openai.OpenAI(api_key=APIConfig.OPENAI_API_KEY)
            
            # 构建DALL-E提示词
            dalle_prompt = f"Create a beautiful, high-quality background image for a video thumbnail about: {prompt}. Style: {style}, 1920x1080 resolution, professional design."
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1792x1024",
                quality="standard",
                n=1
            )
            
            if response.data:
                image_url = response.data[0].url
                
                # 下载图片
                timestamp = int(time.time())
                filename = f"dalle_bg_{timestamp}.png"
                filepath = self.output_dir / filename
                
                img_response = requests.get(image_url)
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                logger.info(f"DALL-E背景生成成功: {filepath}")
                return str(filepath)
            else:
                logger.error("DALL-E背景生成失败")
                return None
                
        except Exception as e:
            logger.error(f"DALL-E背景生成异常: {e}")
            return self._generate_default_background()
    
    def generate_midjourney_background(self, prompt: str, style: str = "modern") -> Optional[str]:
        """使用Midjourney生成背景图片"""
        logger.info(f"开始使用Midjourney生成背景: {prompt}")
        
        # 这里需要集成Midjourney API
        # 由于Midjourney API比较复杂，这里使用模拟实现
        logger.warning("Midjourney API未实现，使用默认背景")
        return self._generate_default_background()
    
    def _generate_default_background(self) -> str:
        """生成默认背景"""
        timestamp = int(time.time())
        filename = f"default_bg_{timestamp}.png"
        filepath = self.output_dir / filename
        
        # 创建默认背景
        img = Image.new('RGB', (1920, 1080), color=(25, 25, 35))
        img.save(filepath)
        
        logger.info(f"生成默认背景: {filepath}")
        return str(filepath)
    
    def add_text_to_image(self, image_path: str, text: str, 
                          output_path: str, template: str = "default") -> bool:
        """在图片上添加文字"""
        logger.info(f"开始添加文字到图片: {text}")
        
        try:
            # 打开图片
            img = Image.open(image_path)
            
            # 获取模板配置
            template_config = self.templates.get(template, self.templates["default"])
            
            # 创建绘图对象
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", template_config["font_size"])
            except:
                font = ImageFont.load_default()
            
            # 计算文字位置（居中）
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            
            # 绘制文字阴影
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), text, 
                     fill=(0, 0, 0), font=font)
            
            # 绘制文字
            draw.text((x, y), text, 
                     fill=template_config["text_color"], font=font)
            
            # 保存图片
            img.save(output_path)
            
            logger.info(f"文字添加成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"文字添加失败: {e}")
            return False
    
    def add_logo_to_image(self, image_path: str, logo_path: str, 
                          output_path: str, position: str = "top-right") -> bool:
        """在图片上添加LOGO"""
        logger.info(f"开始添加LOGO: {logo_path}")
        
        try:
            # 打开图片
            img = Image.open(image_path)
            logo = Image.open(logo_path)
            
            # 调整LOGO大小
            logo_size = (200, 100)
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
            
            # 计算LOGO位置
            if position == "top-right":
                x = img.width - logo_size[0] - 20
                y = 20
            elif position == "top-left":
                x = 20
                y = 20
            elif position == "bottom-right":
                x = img.width - logo_size[0] - 20
                y = img.height - logo_size[1] - 20
            elif position == "bottom-left":
                x = 20
                y = img.height - logo_size[1] - 20
            else:
                x = 20
                y = 20
            
            # 粘贴LOGO
            img.paste(logo, (x, y), logo if logo.mode == 'RGBA' else None)
            
            # 保存图片
            img.save(output_path)
            
            logger.info(f"LOGO添加成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"LOGO添加失败: {e}")
            return False
    
    def create_thumbnail_with_canva(self, title: str, background_prompt: str, 
                                   template: str = "default") -> Optional[str]:
        """使用Canva API创建封面"""
        logger.info(f"开始使用Canva创建封面: {title}")
        
        # 这里需要集成Canva API
        # 由于Canva API比较复杂，这里使用模拟实现
        logger.warning("Canva API未实现，使用本地生成")
        return self.create_thumbnail_local(title, background_prompt, template)
    
    def create_thumbnail_local(self, title: str, background_prompt: str, 
                              template: str = "default") -> Optional[str]:
        """本地创建封面"""
        logger.info(f"开始本地创建封面: {title}")
        
        try:
            # 1. 生成背景
            background_path = self.generate_dalle_background(background_prompt, template)
            if not background_path:
                logger.error("背景生成失败")
                return None
            
            # 2. 添加文字
            timestamp = int(time.time())
            text_filename = f"thumbnail_text_{timestamp}.png"
            text_path = self.output_dir / text_filename
            
            if not self.add_text_to_image(background_path, title, str(text_path), template):
                logger.error("文字添加失败")
                return None
            
            # 3. 添加LOGO（如果有）
            logo_path = Path("assets/logo.png")
            if logo_path.exists():
                final_filename = f"thumbnail_final_{timestamp}.png"
                final_path = self.output_dir / final_filename
                
                if not self.add_logo_to_image(str(text_path), str(logo_path), str(final_path)):
                    logger.error("LOGO添加失败")
                    return None
                
                return str(final_path)
            else:
                return str(text_path)
                
        except Exception as e:
            logger.error(f"本地创建封面失败: {e}")
            return None
    
    def batch_create_thumbnails(self, video_data_list: List[Dict]) -> List[Dict]:
        """批量创建封面"""
        logger.info(f"开始批量创建封面，共 {len(video_data_list)} 个")
        
        results = []
        
        for i, video_data in enumerate(video_data_list):
            logger.info(f"创建第 {i+1}/{len(video_data_list)} 个封面")
            
            title = video_data.get('title', '')
            background_prompt = video_data.get('background_prompt', '')
            template = video_data.get('template', 'default')
            
            if not title:
                logger.warning(f"视频标题为空，跳过: {video_data}")
                continue
            
            # 创建封面
            thumbnail_path = self.create_thumbnail_local(title, background_prompt, template)
            
            result = {
                "video_id": i,
                "title": title,
                "thumbnail_path": thumbnail_path,
                "template": template,
                "status": "success" if thumbnail_path else "failed",
                "create_time": time.time()
            }
            
            results.append(result)
        
        logger.info(f"批量封面创建完成，成功: {len([r for r in results if r['status'] == 'success'])}")
        return results
    
    def get_available_templates(self) -> List[Dict]:
        """获取可用的模板列表"""
        return [
            {
                "id": "default",
                "name": "默认模板",
                "description": "简洁的默认封面模板"
            },
            {
                "id": "modern",
                "name": "现代模板",
                "description": "现代风格的封面模板"
            },
            {
                "id": "vintage",
                "name": "复古模板",
                "description": "复古风格的封面模板"
            }
        ]

def main():
    """主函数"""
    generator = ThumbnailGenerator()
    
    # 示例视频数据
    sample_video_data = [
        {
            "title": "AI技术突破：新算法大幅提升准确率",
            "background_prompt": "artificial intelligence technology breakthrough",
            "template": "modern"
        },
        {
            "title": "科技新闻：最新技术发展趋势",
            "background_prompt": "technology news trends",
            "template": "default"
        }
    ]
    
    # 批量创建封面
    results = generator.batch_create_thumbnails(sample_video_data)
    
    logger.info(f"封面创建完成，共创建 {len(results)} 个封面")

if __name__ == "__main__":
    main() 