#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配音生成模块
"""

import requests
import json
import time
from pathlib import Path
from loguru import logger
from typing import Dict, Optional, List
from config import APIConfig

class TTSGenerator:
    """TTS生成器"""
    
    def __init__(self):
        self.output_dir = Path("data/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 音色配置
        self.voice_options = {
            "male": {
                "name": "男声",
                "voice_id": "male_voice_001",
                "speed": 1.0,
                "emotion": "neutral"
            },
            "female": {
                "name": "女声", 
                "voice_id": "female_voice_001",
                "speed": 1.0,
                "emotion": "neutral"
            },
            "child": {
                "name": "童声",
                "voice_id": "child_voice_001", 
                "speed": 1.2,
                "emotion": "happy"
            }
        }
    
    def generate_tts_fliki(self, text: str, voice_type: str = "female", 
                           speed: float = 1.0, emotion: str = "neutral") -> Optional[str]:
        """使用Fliki API生成TTS"""
        logger.info(f"开始使用Fliki生成TTS，音色: {voice_type}")
        
        if not APIConfig.FLIKI_API_KEY:
            logger.warning("Fliki API密钥未配置，使用模拟数据")
            return self._generate_mock_audio(text, voice_type)
        
        try:
            # Fliki API调用（示例）
            url = "https://api.fliki.ai/v1/tts"
            headers = {
                "Authorization": f"Bearer {APIConfig.FLIKI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            voice_config = self.voice_options.get(voice_type, self.voice_options["female"])
            
            data = {
                "text": text,
                "voice_id": voice_config["voice_id"],
                "speed": speed,
                "emotion": emotion,
                "format": "mp3"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                # 保存音频文件
                timestamp = int(time.time())
                filename = f"fliki_{voice_type}_{timestamp}.mp3"
                filepath = self.output_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Fliki TTS生成成功: {filepath}")
                return str(filepath)
            else:
                logger.error(f"Fliki TTS生成失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Fliki TTS生成异常: {e}")
            return self._generate_mock_audio(text, voice_type)
    
    def generate_tts_heygen(self, text: str, voice_type: str = "female",
                            speed: float = 1.0, emotion: str = "neutral") -> Optional[str]:
        """使用Heygen API生成TTS"""
        logger.info(f"开始使用Heygen生成TTS，音色: {voice_type}")
        
        if not APIConfig.HEYGEN_API_KEY:
            logger.warning("Heygen API密钥未配置，使用模拟数据")
            return self._generate_mock_audio(text, voice_type)
        
        try:
            # Heygen API调用（示例）
            url = "https://api.heygen.com/v1/tts"
            headers = {
                "Authorization": f"Bearer {APIConfig.HEYGEN_API_KEY}",
                "Content-Type": "application/json"
            }
            
            voice_config = self.voice_options.get(voice_type, self.voice_options["female"])
            
            data = {
                "text": text,
                "voice_id": voice_config["voice_id"],
                "speed": speed,
                "emotion": emotion,
                "format": "mp3"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                # 保存音频文件
                timestamp = int(time.time())
                filename = f"heygen_{voice_type}_{timestamp}.mp3"
                filepath = self.output_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Heygen TTS生成成功: {filepath}")
                return str(filepath)
            else:
                logger.error(f"Heygen TTS生成失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Heygen TTS生成异常: {e}")
            return self._generate_mock_audio(text, voice_type)
    
    def _generate_mock_audio(self, text: str, voice_type: str) -> str:
        """生成模拟音频文件（用于测试）"""
        timestamp = int(time.time())
        filename = f"mock_{voice_type}_{timestamp}.mp3"
        filepath = self.output_dir / filename
        
        # 创建一个模拟的音频文件（实际使用时需要真实的音频生成）
        with open(filepath, 'wb') as f:
            # 写入一些模拟数据
            f.write(b'mock_audio_data')
        
        logger.info(f"生成模拟音频文件: {filepath}")
        return str(filepath)
    
    def batch_generate_tts(self, scripts: List[Dict], voice_type: str = "female") -> List[Dict]:
        """批量生成TTS"""
        logger.info(f"开始批量生成TTS，共 {len(scripts)} 个文案")
        
        results = []
        
        for i, script_data in enumerate(scripts):
            logger.info(f"处理第 {i+1}/{len(scripts)} 个文案")
            
            script = script_data.get('script', '')
            if not script:
                continue
            
            # 生成TTS
            audio_path = self.generate_tts_fliki(script, voice_type)
            
            if audio_path:
                result = {
                    "script_id": i,
                    "script_title": script_data.get('title', ''),
                    "audio_path": audio_path,
                    "voice_type": voice_type,
                    "generate_time": time.time(),
                    "status": "success"
                }
            else:
                result = {
                    "script_id": i,
                    "script_title": script_data.get('title', ''),
                    "audio_path": None,
                    "voice_type": voice_type,
                    "generate_time": time.time(),
                    "status": "failed"
                }
            
            results.append(result)
            
            # 添加延迟避免API限制
            time.sleep(1)
        
        logger.info(f"批量TTS生成完成，成功: {len([r for r in results if r['status'] == 'success'])}")
        return results
    
    def save_tts_info(self, tts_results: List[Dict]) -> str:
        """保存TTS信息到文件"""
        timestamp = int(time.time())
        filename = f"tts_results_{timestamp}.json"
        filepath = Path("data") / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tts_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"TTS信息已保存到: {filepath}")
        return str(filepath)

def main():
    """主函数"""
    generator = TTSGenerator()
    
    # 示例文案
    sample_scripts = [
        {
            "title": "AI技术突破",
            "script": "今天我们来聊聊AI技术的最新突破..."
        },
        {
            "title": "科技新闻",
            "script": "最新的科技新闻显示..."
        }
    ]
    
    # 批量生成TTS
    results = generator.batch_generate_tts(sample_scripts, "female")
    
    # 保存结果
    generator.save_tts_info(results)
    
    logger.info(f"TTS生成完成，共生成 {len(results)} 个音频文件")

if __name__ == "__main__":
    main() 