#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频剪辑与合成模块
"""

import subprocess
import json
import time
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional, Tuple
from config import VideoConfig

class VideoEditor:
    """视频编辑器"""
    
    def __init__(self):
        self.output_dir = Path("data/edited_videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def crop_video(self, input_path: str, output_path: str, 
                   start_time: float = 0, duration: float = None) -> bool:
        """裁剪视频"""
        logger.info(f"开始裁剪视频: {input_path}")
        
        try:
            cmd = [
                "ffmpeg", "-i", input_path,
                "-ss", str(start_time)
            ]
            
            if duration:
                cmd.extend(["-t", str(duration)])
            
            cmd.extend([
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y", output_path
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"视频裁剪成功: {output_path}")
                return True
            else:
                logger.error(f"视频裁剪失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"视频裁剪异常: {e}")
            return False
    
    def merge_audio_video(self, video_path: str, audio_path: str, 
                         output_path: str) -> bool:
        """合成音视频"""
        logger.info(f"开始合成音视频: {video_path} + {audio_path}")
        
        try:
            cmd = [
                "ffmpeg", "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-y", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"音视频合成成功: {output_path}")
                return True
            else:
                logger.error(f"音视频合成失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"音视频合成异常: {e}")
            return False
    
    def add_subtitle(self, video_path: str, subtitle_text: str, 
                    output_path: str) -> bool:
        """添加字幕"""
        logger.info(f"开始添加字幕: {video_path}")
        
        try:
            # 创建字幕文件
            subtitle_file = self.temp_dir / "subtitle.srt"
            self._create_srt_file(subtitle_text, subtitle_file)
            
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vf", f"subtitles={subtitle_file}",
                "-c:a", "copy",
                "-y", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"字幕添加成功: {output_path}")
                return True
            else:
                logger.error(f"字幕添加失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"字幕添加异常: {e}")
            return False
    
    def _create_srt_file(self, text: str, output_path: Path):
        """创建SRT字幕文件"""
        lines = text.split('\n')
        srt_content = ""
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                start_time = i * 3  # 每行显示3秒
                end_time = start_time + 3
                
                srt_content += f"{i}\n"
                srt_content += f"{start_time:02d}:00:00,000 --> {end_time:02d}:00:00,000\n"
                srt_content += f"{line}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
    
    def add_logo(self, video_path: str, logo_path: str, 
                 output_path: str, position: str = "top-right") -> bool:
        """添加LOGO"""
        logger.info(f"开始添加LOGO: {video_path}")
        
        try:
            # 根据位置设置LOGO坐标
            position_map = {
                "top-left": "10:10",
                "top-right": "W-w-10:10",
                "bottom-left": "10:H-h-10",
                "bottom-right": "W-w-10:H-h-10"
            }
            
            logo_pos = position_map.get(position, "10:10")
            
            cmd = [
                "ffmpeg", "-i", video_path,
                "-i", logo_path,
                "-filter_complex", f"[0:v][1:v]overlay={logo_pos}",
                "-c:a", "copy",
                "-y", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"LOGO添加成功: {output_path}")
                return True
            else:
                logger.error(f"LOGO添加失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"LOGO添加异常: {e}")
            return False
    
    def add_transition_effects(self, video_path: str, output_path: str, 
                              effect_type: str = "fade") -> bool:
        """添加转场特效"""
        logger.info(f"开始添加转场特效: {effect_type}")
        
        try:
            if effect_type == "fade":
                # 淡入淡出效果
                cmd = [
                    "ffmpeg", "-i", video_path,
                    "-vf", "fade=t=in:st=0:d=1,fade=t=out:st=8:d=1",
                    "-c:a", "copy",
                    "-y", output_path
                ]
            elif effect_type == "zoom":
                # 缩放效果
                cmd = [
                    "ffmpeg", "-i", video_path,
                    "-vf", "zoompan=z='min(zoom+0.0015,1.5)':d=125",
                    "-c:a", "copy",
                    "-y", output_path
                ]
            else:
                logger.warning(f"未知的特效类型: {effect_type}")
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"转场特效添加成功: {output_path}")
                return True
            else:
                logger.error(f"转场特效添加失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"转场特效添加异常: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict:
        """获取视频信息"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"获取视频信息失败: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"获取视频信息异常: {e}")
            return {}
    
    def process_video_pipeline(self, video_path: str, audio_path: str,
                              script_text: str, output_path: str) -> bool:
        """完整的视频处理流水线"""
        logger.info("开始视频处理流水线")
        
        try:
            # 1. 裁剪视频（如果需要）
            cropped_video = self.temp_dir / "cropped_video.mp4"
            if not self.crop_video(video_path, str(cropped_video), duration=60):
                logger.error("视频裁剪失败")
                return False
            
            # 2. 合成音视频
            merged_video = self.temp_dir / "merged_video.mp4"
            if not self.merge_audio_video(str(cropped_video), audio_path, str(merged_video)):
                logger.error("音视频合成失败")
                return False
            
            # 3. 添加字幕
            subtitled_video = self.temp_dir / "subtitled_video.mp4"
            if not self.add_subtitle(str(merged_video), script_text, str(subtitled_video)):
                logger.error("字幕添加失败")
                return False
            
            # 4. 添加LOGO（如果有）
            logo_path = Path("assets/logo.png")
            if logo_path.exists():
                logo_video = self.temp_dir / "logo_video.mp4"
                if not self.add_logo(str(subtitled_video), str(logo_path), str(logo_video)):
                    logger.error("LOGO添加失败")
                    return False
                final_video = logo_video
            else:
                final_video = subtitled_video
            
            # 5. 添加转场特效
            if not self.add_transition_effects(str(final_video), output_path):
                logger.error("转场特效添加失败")
                return False
            
            # 6. 清理临时文件
            self._cleanup_temp_files()
            
            logger.info("视频处理流水线完成")
            return True
            
        except Exception as e:
            logger.error(f"视频处理流水线异常: {e}")
            return False
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for temp_file in self.temp_dir.glob("*"):
                temp_file.unlink()
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def batch_process_videos(self, video_data_list: List[Dict]) -> List[Dict]:
        """批量处理视频"""
        logger.info(f"开始批量处理视频，共 {len(video_data_list)} 个")
        
        results = []
        
        for i, video_data in enumerate(video_data_list):
            logger.info(f"处理第 {i+1}/{len(video_data_list)} 个视频")
            
            video_path = video_data.get('video_path', '')
            audio_path = video_data.get('audio_path', '')
            script_text = video_data.get('script_text', '')
            
            if not all([video_path, audio_path, script_text]):
                logger.warning(f"视频数据不完整，跳过: {video_data}")
                continue
            
            # 生成输出文件名
            timestamp = int(time.time())
            output_filename = f"edited_video_{i}_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            # 处理视频
            success = self.process_video_pipeline(
                video_path, audio_path, script_text, str(output_path)
            )
            
            result = {
                "video_id": i,
                "input_video": video_path,
                "input_audio": audio_path,
                "output_video": str(output_path) if success else None,
                "status": "success" if success else "failed",
                "process_time": time.time()
            }
            
            results.append(result)
        
        logger.info(f"批量视频处理完成，成功: {len([r for r in results if r['status'] == 'success'])}")
        return results

def main():
    """主函数"""
    editor = VideoEditor()
    
    # 示例视频数据
    sample_video_data = [
        {
            "video_path": "data/videos/sample_video.mp4",
            "audio_path": "data/audio/sample_audio.mp3",
            "script_text": "这是一个示例视频的解说文案..."
        }
    ]
    
    # 批量处理视频
    results = editor.batch_process_videos(sample_video_data)
    
    logger.info(f"视频处理完成，共处理 {len(results)} 个视频")

if __name__ == "__main__":
    main() 