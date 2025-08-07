#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容处理器
支持对采集到的内容进行各种加工处理
"""

import logging
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import jieba
from collections import Counter

logger = logging.getLogger(__name__)

class ContentProcessor:
    """内容处理器类"""
    
    def __init__(self):
        self.processing_tasks = {}
    
    def create_batch_task(self, content_ids: List[str], process_type: str, params: Dict[str, Any]) -> str:
        """创建批量处理任务"""
        task_id = str(uuid.uuid4())
        
        task_info = {
            'id': task_id,
            'content_ids': content_ids,
            'process_type': process_type,
            'params': params,
            'status': 'pending',
            'created_time': datetime.now().isoformat(),
            'progress': 0,
            'total': len(content_ids),
            'completed': 0,
            'failed': 0,
            'results': []
        }
        
        self.processing_tasks[task_id] = task_info
        
        # 异步开始处理
        asyncio.create_task(self._process_batch(task_id))
        
        return task_id
    
    async def _process_batch(self, task_id: str):
        """异步批量处理内容"""
        task_info = self.processing_tasks.get(task_id)
        if not task_info:
            return
        
        try:
            task_info['status'] = 'processing'
            
            from content_storage import content_storage
            
            for i, content_id in enumerate(task_info['content_ids']):
                try:
                    # 获取内容
                    article = content_storage.get_article_by_id(content_id)
                    if not article:
                        task_info['failed'] += 1
                        continue
                    
                    # 根据处理类型进行处理
                    result = await self._process_single_content(
                        article, 
                        task_info['process_type'], 
                        task_info['params']
                    )
                    
                    if result['success']:
                        # 保存处理结果
                        processed_article = result['data']
                        content_storage.save_processed_article(content_id, processed_article)
                        task_info['completed'] += 1
                    else:
                        task_info['failed'] += 1
                    
                    task_info['results'].append({
                        'content_id': content_id,
                        'success': result['success'],
                        'message': result.get('message', ''),
                        'data': result.get('data', {})
                    })
                    
                except Exception as e:
                    logger.error(f"处理内容 {content_id} 失败: {e}")
                    task_info['failed'] += 1
                    task_info['results'].append({
                        'content_id': content_id,
                        'success': False,
                        'message': str(e)
                    })
                
                # 更新进度
                task_info['progress'] = int((i + 1) / task_info['total'] * 100)
            
            task_info['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"批量处理任务 {task_id} 失败: {e}")
            task_info['status'] = 'failed'
            task_info['error'] = str(e)
    
    async def _process_single_content(self, article: Dict[str, Any], process_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个内容"""
        try:
            if process_type == 'rewrite':
                return await self._rewrite_content(article, params)
            elif process_type == 'summarize':
                return await self._summarize_content(article, params)
            elif process_type == 'translate':
                return await self._translate_content(article, params)
            elif process_type == 'extract_keywords':
                return await self._extract_keywords(article, params)
            else:
                return {'success': False, 'message': f'不支持的处理类型: {process_type}'}
        
        except Exception as e:
            logger.error(f"处理内容失败: {e}")
            return {'success': False, 'message': str(e)}
    
    async def _rewrite_content(self, article: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """改写内容"""
        style = params.get('style', 'formal')
        content = article.get('content', '')
        
        if not content:
            return {'success': False, 'message': '内容为空'}
        
        # 模拟改写处理（实际项目中可以接入AI改写服务）
        rewritten_content = self._simulate_rewrite(content, style)
        
        processed_article = article.copy()
        processed_article.update({
            'content': rewritten_content,
            'original_content': content,
            'process_type': 'rewrite',
            'process_params': params,
            'processed_time': datetime.now().isoformat(),
            'status': 'processed'
        })
        
        return {
            'success': True,
            'message': '改写完成',
            'data': processed_article
        }
    
    async def _summarize_content(self, article: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要"""
        length = params.get('length', 'medium')
        content = article.get('content', '')
        
        if not content:
            return {'success': False, 'message': '内容为空'}
        
        # 模拟摘要生成
        summary = self._simulate_summarize(content, length)
        
        processed_article = article.copy()
        processed_article.update({
            'summary': summary,
            'process_type': 'summarize',
            'process_params': params,
            'processed_time': datetime.now().isoformat(),
            'status': 'processed'
        })
        
        return {
            'success': True,
            'message': '摘要生成完成',
            'data': processed_article
        }
    
    async def _translate_content(self, article: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """翻译内容"""
        target_language = params.get('target_language', 'en')
        content = article.get('content', '')
        
        if not content:
            return {'success': False, 'message': '内容为空'}
        
        # 模拟翻译处理
        translated_content = self._simulate_translate(content, target_language)
        
        processed_article = article.copy()
        processed_article.update({
            'translated_content': translated_content,
            'target_language': target_language,
            'original_content': content,
            'process_type': 'translate',
            'process_params': params,
            'processed_time': datetime.now().isoformat(),
            'status': 'processed'
        })
        
        return {
            'success': True,
            'message': '翻译完成',
            'data': processed_article
        }
    
    async def _extract_keywords(self, article: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键词"""
        content = article.get('content', '')
        title = article.get('title', '')
        
        if not content and not title:
            return {'success': False, 'message': '内容为空'}
        
        # 提取关键词
        keywords = self._extract_keywords_from_text(content + ' ' + title)
        
        processed_article = article.copy()
        processed_article.update({
            'keywords': keywords,
            'process_type': 'extract_keywords',
            'process_params': params,
            'processed_time': datetime.now().isoformat(),
            'status': 'processed'
        })
        
        return {
            'success': True,
            'message': '关键词提取完成',
            'data': processed_article
        }
    
    def _simulate_rewrite(self, content: str, style: str) -> str:
        """模拟改写内容"""
        # 这里是简单的模拟，实际项目中应该接入AI改写服务
        style_prefixes = {
            'formal': '据报道，',
            'casual': '听说，',
            'professional': '根据专业分析，',
            'creative': '有趣的是，'
        }
        
        prefix = style_prefixes.get(style, '')
        
        # 简单的句子重组
        sentences = re.split(r'[。！？]', content)
        rewritten_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                # 简单的同义词替换和句式调整
                rewritten = sentence.strip()
                rewritten = rewritten.replace('表示', '指出')
                rewritten = rewritten.replace('认为', '表示')
                rewritten = rewritten.replace('显示', '表明')
                rewritten_sentences.append(rewritten)
        
        rewritten_content = prefix + '。'.join(rewritten_sentences)
        if rewritten_content and not rewritten_content.endswith('。'):
            rewritten_content += '。'
        
        return rewritten_content
    
    def _simulate_summarize(self, content: str, length: str) -> str:
        """模拟生成摘要"""
        # 简单的摘要生成逻辑
        sentences = re.split(r'[。！？]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return "无法生成摘要"
        
        # 根据长度选择句子数量
        length_map = {
            'short': min(2, len(sentences)),
            'medium': min(4, len(sentences)),
            'long': min(6, len(sentences))
        }
        
        num_sentences = length_map.get(length, 3)
        
        # 选择前几个句子作为摘要
        summary_sentences = sentences[:num_sentences]
        return '。'.join(summary_sentences) + '。'
    
    def _simulate_translate(self, content: str, target_language: str) -> str:
        """模拟翻译内容"""
        # 这里是简单的模拟，实际项目中应该接入翻译服务
        language_prefixes = {
            'en': '[English Translation] ',
            'ja': '[日本語翻訳] ',
            'ko': '[한국어 번역] ',
            'fr': '[Traduction française] ',
            'de': '[Deutsche Übersetzung] '
        }
        
        prefix = language_prefixes.get(target_language, '[Translation] ')
        return prefix + content[:200] + '...'  # 模拟翻译结果
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        try:
            # 使用jieba进行中文分词
            words = jieba.lcut(text)
            
            # 过滤停用词和短词
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            
            filtered_words = [
                word for word in words 
                if len(word) > 1 and word not in stop_words and word.isalnum()
            ]
            
            # 统计词频并返回前10个关键词
            word_freq = Counter(filtered_words)
            keywords = [word for word, freq in word_freq.most_common(10)]
            
            return keywords
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.processing_tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有处理任务"""
        return list(self.processing_tasks.values())

# 全局内容处理器实例
content_processor = ContentProcessor()