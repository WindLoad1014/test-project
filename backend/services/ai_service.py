"""
AI服务
集成意图分类、相似案例检索、回复生成等功能
"""
import json
import sys
import os
from typing import List, Dict, Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db_manager import DatabaseManager
from backend.config import Config


class AIService:
    """AI服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._init_components()
    
    def _init_components(self):
        """初始化AI组件"""
        try:
            # 导入核心模块 - 直接从backend目录导入
            from retriever import RetrieverFactory, search_similar_cases
            from intent_classifier import IntentClassifier
            from llm_generator import LLMGenerator
            
            self.retriever = RetrieverFactory.get_retriever('keyword')
            self.classifier = IntentClassifier()
            self.llm_generator = LLMGenerator(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL
            )
            
            print("✅ AI组件初始化完成")
            
        except Exception as e:
            print(f"⚠️ AI组件初始化失败: {e}")
            self.retriever = None
            self.classifier = None
            self.llm_generator = None
    
    def analyze_email(self, email: Dict) -> Dict:
        """
        分析邮件
        包括意图分类、紧急度判断、相似案例检索
        """
        content = email.get('content', '')
        
        # 解析邮件内容
        parsed = self._parse_email_content(content)
        question = parsed.get('question_content', content[:200])
        
        # 意图分类
        if self.classifier:
            intent_result = self.classifier.classify(
                question,
                parsed.get('question_type', '')
            )
        else:
            intent_result = self._fallback_classification(question)
        
        # 检索相似案例
        similar_cases = self.search_similar_cases(
            query=question,
            top_k=5,
            question_type=intent_result.get('question_type')
        )
        
        # 整合分析结果
        analysis = {
            'question_type': intent_result.get('question_type', '其他'),
            'question_type_confidence': intent_result.get('question_type_confidence', 0.5),
            'urgency': intent_result.get('urgency', 'medium'),
            'urgency_confidence': intent_result.get('urgency_confidence', 0.5),
            'urgency_reason': intent_result.get('urgency_reason', ''),
            'sentiment': intent_result.get('sentiment', 'neutral'),
            'sentiment_confidence': intent_result.get('sentiment_confidence', 0.5),
            'suggestions': intent_result.get('suggestions', []),
            'similar_cases': similar_cases,
            'parsed_info': parsed
        }
        
        return analysis
    
    def search_similar_cases(self, query: str, top_k: int = 5, question_type: str = None, fuzzy: bool = True) -> List[Dict]:
        """检索相似案例（支持模糊搜索）"""
        if self.retriever:
            try:
                results = self.retriever.search(query, top_k=top_k, question_type=question_type, fuzzy=fuzzy)
                return results
            except Exception as e:
                print(f"检索失败: {e}")
        
        # 降级方案：从数据库查询
        return self._fallback_search(query, top_k)
    
    def generate_reply(self, email: Dict, analysis: Dict, use_llm: bool = True) -> Dict:
        """
        生成回复
        """
        question = analysis.get('parsed_info', {}).get('question_content', email.get('content', '')[:200])
        similar_cases = analysis.get('similar_cases', [])
        question_type = analysis.get('question_type', '其他')
        
        if use_llm and self.llm_generator and Config.OPENAI_API_KEY:
            try:
                result = self.llm_generator.generate_with_fallback(
                    player_question=question,
                    similar_cases=similar_cases,
                    question_type=question_type
                )
                
                return {
                    'content': result.get('content', result['response']),  # 日语内容
                    'content_zh': result.get('content_zh', ''),  # 中文内容
                    'bilingual': result.get('bilingual', {}),  # 完整双语内容
                    'model': result['model'],
                    'confidence': 0.9 if result.get('success') else 0.5,
                    'is_fallback': result.get('is_fallback', False),
                    'cached': result.get('cached', False)
                }
                
            except Exception as e:
                print(f"LLM生成失败: {e}")
        
        # 模板降级方案
        return self._generate_template_reply(question_type, similar_cases)
    
    def _parse_email_content(self, content: str) -> Dict:
        """解析邮件内容"""
        import re
        
        result = {}
        patterns = {
            'account_id': r'アカウントID\s*[:：]\s*(\S*)',
            'player_name': r'プレイヤー名\s*[:：]\s*(\S*)',
            'app_version': r'アプリバージョン\s*[:：]\s*(\S*)',
            'os_version': r'ご利用のOSバージョン\s*[:：]\s*(\S*)',
            'device': r'ご利用端末名\s*[:：]\s*([^\n]+)',
            'question_type': r'お問い合わせ内容の種類\s*[:：]\s*([^\n]+)',
            'platform': r'ご利用環境\s*[:：]\s*(\S*)',
            'question_content': r'お問い合わせ内容\s*[:：]\s*([\s\S]+?)(?:添付ファイル|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, str(content))
            result[key] = match.group(1).strip() if match else ''
        
        return result
    
    def _fallback_classification(self, text: str) -> Dict:
        """降级分类方案"""
        # 简单的关键词匹配
        text_lower = text.lower()
        
        # 紧急度判断
        urgent_keywords = ['至急', '急ぎ', 'すぐに', '今すぐ', 'bug', 'error', 'crash']
        urgency = 'high' if any(k in text_lower for k in urgent_keywords) else 'medium'
        
        # 问题类型
        if any(k in text_lower for k in ['購入', '課金', 'ダイヤ', '課金']):
            question_type = '充值问题'
        elif any(k in text_lower for k in ['バグ', 'bug', 'エラー', 'error']):
            question_type = 'BUG反馈'
        elif any(k in text_lower for k in ['要望', '提案', '改善']):
            question_type = '意见建议'
        else:
            question_type = '其他'
        
        return {
            'question_type': question_type,
            'question_type_confidence': 0.6,
            'urgency': urgency,
            'urgency_confidence': 0.6,
            'urgency_reason': '基于关键词匹配',
            'sentiment': 'neutral',
            'sentiment_confidence': 0.5,
            'suggestions': ['请人工复核']
        }
    
    def _fallback_search(self, query: str, top_k: int) -> List[Dict]:
        """降级检索方案"""
        # 从数据库查询知识库
        results = self.db.fetch_all(
            "SELECT * FROM knowledge_base ORDER BY usage_count DESC LIMIT ?",
            (top_k,)
        )
        
        return [
            {
                'question': r['question'],
                'answer': r['answer'],
                'similarity': 0.5,
                'question_type_cn': r.get('question_type', '其他'),
                'platform': r.get('platform', '未知')
            }
            for r in results
        ]
    
    def _generate_template_reply(self, question_type: str, similar_cases: List[Dict]) -> Dict:
        """模板回复生成（支持中日双语）"""
        templates = {
            '充值问题': """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

{solution}

ご迷惑をおかけしておりますことを深くお詫び申し上げます。
至急調査いたしますので、今しばらくお待ちくださいますようお願いいたします。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。""",
            'BUG反馈': """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

ご報告いただいた事象について、調査いたします。

{solution}

調査結果については、追ってご連絡いたします。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。""",
            '意见建议': """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

貴重なご意見をいただき、ありがとうございます。

{solution}

いただいたご意見は、開発チームに共有させていただきます。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。"""
        }
        
        templates_zh = {
            '充值问题': """感谢您一直以来使用我们的服务。
这里是『ぽちゃガチョ！』客服支持。

{solution}

对于给您带来的不便，我们深表歉意。
我们会紧急调查此事，请您稍等片刻。

今后也请多多关照『ぽちゃガチョ！』。""",
            'BUG反馈': """感谢您一直以来使用我们的服务。
这里是『ぽちゃガチョ！』客服支持。

关于您报告的问题，我们会进行调查。

{solution}

调查结果我们会后续联系您。

今后也请多多关照『ぽちゃガチョ！』。""",
            '意见建议': """感谢您一直以来使用我们的服务。
这里是『ぽちゃガチョ！』客服支持。

感谢您的宝贵意见。

{solution}

您的意见我们会分享给开发团队。

今后也请多多关照『ぽちゃガチョ！』。"""
        }
        
        template = templates.get(question_type, templates['意见建议'])
        template_zh = templates_zh.get(question_type, templates_zh['意见建议'])
        
        if similar_cases:
            solution = similar_cases[0]['answer'][:500]
            solution_zh = similar_cases[0]['answer'][:500]  # 简化处理，实际应该翻译
        else:
            solution = "ご連絡いただきありがとうございます。"
            solution_zh = "感谢您的联系。"
        
        content = template.format(solution=solution)
        content_zh = template_zh.format(solution=solution_zh)
        
        return {
            'content': content,
            'content_zh': content_zh,
            'bilingual': {
                'japanese': content,
                'chinese': content_zh,
                'full_text': f"【日本語】\n{content}\n\n【中文】\n{content_zh}"
            },
            'model': 'template',
            'confidence': 0.6,
            'is_fallback': True
        }
