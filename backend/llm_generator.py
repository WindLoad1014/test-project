"""
LLM回复生成模块
使用兼容OpenAI API的大模型自动生成客服回复
集成缓存和日志功能
"""
import json
import os
import time
from typing import List, Dict, Optional
try:
    from config import Config
    OPENAI_API_KEY = Config.OPENAI_API_KEY
    OPENAI_BASE_URL = Config.OPENAI_BASE_URL
    LLM_MODEL = Config.LLM_MODEL
except ImportError:
    from backend.config import Config
    OPENAI_API_KEY = Config.OPENAI_API_KEY
    OPENAI_BASE_URL = Config.OPENAI_BASE_URL
    LLM_MODEL = Config.LLM_MODEL

from cache_manager import get_cache
from logger import get_logger, get_monitor


class LLMGenerator:
    """LLM回复生成器：自动生成日语客服回复"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, use_cache: bool = True):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or LLM_MODEL
        self.client = None
        self.use_cache = use_cache
        self.cache = get_cache() if use_cache else None
        self.logger = get_logger()
        self.monitor = get_monitor()
        
    def init_client(self):
        """初始化OpenAI客户端"""
        if self.client is None:
            try:
                from openai import OpenAI
                
                if not self.api_key:
                    raise ValueError("API Key未设置，请在config.py或环境变量中设置OPENAI_API_KEY")
                
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                print(f"✅ LLM客户端初始化完成")
                print(f"   模型: {self.model}")
                print(f"   API地址: {self.base_url}")
            except ImportError:
                print("⚠️ openai库未安装，尝试安装...")
                import subprocess
                subprocess.check_call(["python", "-m", "pip", "install", "openai", "-q"])
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        return self.client
    
    def generate_prompt(self, player_question: str, similar_cases: List[Dict],
                       question_type: str = "") -> str:
        """生成Prompt"""
        
        # 构建相似案例上下文
        cases_text = ""
        for i, case in enumerate(similar_cases[:3], 1):
            cases_text += f"\n案例{i}:\n"
            cases_text += f"  玩家问题: {case['question'][:200]}\n"
            cases_text += f"  客服回复: {case['answer'][:300]}\n"
        
        # 问题类型说明
        type_guidance = {
            "BUG反馈": "表示歉意，说明正在调查，承诺后续联系",
            "意见建议": "感谢反馈，说明会转达给开发团队",
            "充值问题": "表示歉意，承诺紧急调查并尽快解决",
            "账号问题": "提供账号恢复指导，必要时要求提供更多信息",
            "其他": "提供一般性帮助"
        }
        
        guidance = type_guidance.get(question_type, type_guidance["其他"])
        
        prompt = f"""你是一名专业的日本游戏客服，游戏名称是『ぽちゃガチョ！』。

【任务】
根据玩家的咨询内容和历史相似案例，生成一份专业、礼貌的日语回复邮件，并提供中文对照。

【玩家咨询内容】
{player_question}

【历史相似案例参考】
{cases_text}

【问题类型】
{question_type}

【回复要求】
1. 使用标准日语敬语（です/ます体）
2. 开头必须包含："いつもご利用いただきありがとうございます。『ぽちゃガチョ！』サポート担当です。"
3. 根据问题类型处理：{guidance}
4. 结尾必须包含："今後とも『ぽちゃガチョ！』をよろしくお願いいたします。"
5. 语气要亲切、专业、有耐心
6. 如果无法立即解决，要说明正在调查并承诺后续联系

【输出格式】
请严格按照以下格式输出：

【日本語】
（日语回复内容）

【中文】
（中文翻译内容）

注意：必须同时提供日语原文和中文翻译，方便客服人员对照查看。"""
        
        return prompt
    
    def parse_bilingual_response(self, text: str) -> Dict[str, str]:
        """
        解析中日双语回复
        
        Args:
            text: LLM生成的文本
            
        Returns:
            包含日语和中文内容的字典
        """
        japanese = ""
        chinese = ""
        
        # 尝试匹配【日本語】和【中文】标记
        import re
        
        # 匹配【日本語】部分
        ja_match = re.search(r'【日本語】\s*\n?(.*?)\n?(?=【中文】|$)', text, re.DOTALL)
        if ja_match:
            japanese = ja_match.group(1).strip()
        
        # 匹配【中文】部分
        zh_match = re.search(r'【中文】\s*\n?(.*?)\n?(?=【|$)', text, re.DOTALL)
        if zh_match:
            chinese = zh_match.group(1).strip()
        
        # 如果没有匹配到标记，尝试其他格式
        if not japanese and not chinese:
            # 尝试按空行分割
            parts = text.split('\n\n')
            if len(parts) >= 2:
                japanese = parts[0].strip()
                chinese = parts[1].strip()
            else:
                # 默认全部作为日语内容
                japanese = text.strip()
                chinese = "（未提供中文翻译）"
        
        # 如果只有日语没有中文
        if japanese and not chinese:
            chinese = "（未提供中文翻译）"
        
        # 如果只有中文没有日语
        if chinese and not japanese:
            japanese = chinese
            chinese = "（未提供中文翻译）"
        
        return {
            'japanese': japanese,
            'chinese': chinese,
            'full_text': text
        }
    
    def generate_response(self, player_question: str, 
                         similar_cases: List[Dict] = None,
                         question_type: str = "",
                         temperature: float = 0.7,
                         use_cache: bool = None) -> Dict:
        """
        生成回复
        
        Args:
            player_question: 玩家问题
            similar_cases: 相似案例
            question_type: 问题类型
            temperature: 生成温度
            use_cache: 是否使用缓存（默认使用初始化设置）
        """
        start_time = time.time()
        
        # 确定是否使用缓存
        should_use_cache = use_cache if use_cache is not None else self.use_cache
        
        # 检查缓存
        if should_use_cache and self.cache:
            cached_response = self.cache.get(player_question, self.model, question_type=question_type)
            if cached_response:
                duration_ms = (time.time() - start_time) * 1000
                self.monitor.record_cache(hit=True)
                self.logger.log_generation(
                    query=player_question,
                    model=self.model,
                    duration_ms=duration_ms,
                    success=True,
                    cached=True
                )
                return {
                    'success': True,
                    'response': cached_response,
                    'error': None,
                    'model': self.model,
                    'cached': True
                }
            self.monitor.record_cache(hit=False)
        
        # 检查API Key
        if not self.api_key:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_generation(
                query=player_question,
                model=self.model,
                duration_ms=duration_ms,
                success=False,
                error='API Key未设置'
            )
            return {
                'success': False,
                'response': '',
                'error': 'API Key未设置，请在config.py中设置OPENAI_API_KEY',
                'model': self.model
            }
        
        try:
            self.init_client()
            
            # 生成Prompt
            prompt = self.generate_prompt(player_question, similar_cases or [], question_type)
            
            print(f"🤖 调用LLM生成回复...")
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的日本游戏客服，擅长用礼貌的日语回复玩家咨询。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=800,
                timeout=90  # 设置90秒超时
            )
            
            generated_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            print(f"✅ 回复生成完成")
            print(f"   使用token: {tokens_used}")
            
            # 解析中日双语内容
            parsed_content = self.parse_bilingual_response(generated_text)
            
            # 保存到缓存
            if should_use_cache and self.cache:
                self.cache.set(player_question, generated_text, self.model, question_type=question_type)
            
            # 记录性能
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.record_api_call(success=True, tokens=tokens_used)
            self.logger.log_generation(
                query=player_question,
                model=self.model,
                duration_ms=duration_ms,
                success=True,
                tokens_used=tokens_used
            )
            
            return {
                'success': True,
                'response': generated_text,
                'content': parsed_content['japanese'],  # 日语内容（用于发送）
                'content_zh': parsed_content['chinese'],  # 中文内容（对照）
                'bilingual': parsed_content,  # 完整双语内容
                'error': None,
                'model': self.model,
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'cached': False
            }
            
        except Exception as e:
            print(f"❌ LLM生成失败: {str(e)}")
            
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.record_api_call(success=False)
            self.logger.log_generation(
                query=player_question,
                model=self.model,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
            
            return {
                'success': False,
                'response': '',
                'error': str(e),
                'model': self.model
            }
    
    def generate_with_fallback(self, player_question: str,
                               similar_cases: List[Dict] = None,
                               question_type: str = "") -> Dict:
        """生成回复（带降级方案）"""
        
        # 首先尝试LLM生成
        result = self.generate_response(player_question, similar_cases, question_type)
        
        if result['success']:
            return result
        
        # 如果失败，使用模板降级方案
        print("⚠️ LLM生成失败，使用模板降级方案")
        
        try:
            from config import Config
            RESPONSE_TEMPLATES = Config.RESPONSE_TEMPLATES
        except ImportError:
            from backend.config import Config
            RESPONSE_TEMPLATES = Config.RESPONSE_TEMPLATES
        
        # 选择模板
        template_key = None
        for key in RESPONSE_TEMPLATES.keys():
            if key in question_type or question_type in key:
                template_key = key
                break
        
        if not template_key:
            template_key = "意见建议"
        
        template = RESPONSE_TEMPLATES.get(template_key, RESPONSE_TEMPLATES["意见建议"])
        
        # 使用最相似案例的答案作为解决方案
        if similar_cases:
            solution = similar_cases[0]['answer'][:500]
        else:
            solution = "ご迷惑をおかけしておりますことを深くお詫び申し上げます。"
        
        fallback_response = template.format(solution=solution)
        
        # 为降级方案添加中文翻译
        fallback_zh = "【模板降级方案】\n\n" + fallback_response.replace(
            "いつもご利用いただきありがとうございます。『ぽちゃガチョ！』サポート担当です。",
            "感谢您一直以来使用我们的服务。这里是『ぽちゃガチョ！』客服支持。"
        ).replace(
            "今後とも『ぽちゃガチョ！』をよろしくお願いいたします。",
            "今后也请多多关照『ぽちゃガチョ！』。"
        ).replace(
            "ご迷惑をおかけしておりますことを深くお詫び申し上げます。",
            "对于给您带来的不便，我们深表歉意。"
        )
        
        return {
            'success': True,
            'response': fallback_response,
            'content': fallback_response,
            'content_zh': fallback_zh,
            'bilingual': {
                'japanese': fallback_response,
                'chinese': fallback_zh,
                'full_text': f"【日本語】\n{fallback_response}\n\n【中文】\n{fallback_zh}"
            },
            'error': None,
            'model': 'template_fallback',
            'is_fallback': True,
            'original_error': result.get('error')
        }
    
    def batch_generate(self, questions: List[Dict]) -> List[Dict]:
        """批量生成回复"""
        results = []
        
        print(f"\n{'='*80}")
        print(f"🔄 批量生成: {len(questions)} 个问题")
        print(f"{'='*80}\n")
        
        for i, item in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] 处理问题...")
            result = self.generate_response(
                player_question=item['question'],
                similar_cases=item.get('similar_cases', []),
                question_type=item.get('question_type', '')
            )
            results.append({
                'question': item['question'],
                'result': result
            })
            print()
        
        # 统计
        success_count = sum(1 for r in results if r['result']['success'])
        print(f"\n✅ 批量生成完成: {success_count}/{len(questions)} 成功")
        
        return results
    
    def get_stats(self) -> Dict:
        """获取生成器统计信息"""
        cache_stats = self.cache.get_stats() if self.cache else {}
        monitor_stats = self.monitor.get_metrics()
        
        return {
            'cache': cache_stats,
            'performance': monitor_stats,
            'model': self.model
        }


if __name__ == "__main__":
    # 测试
    print("="*80)
    print("🤖 LLM生成器测试（带缓存和日志）")
    print("="*80)
    
    generator = LLMGenerator()
    
    # 测试生成
    test_question = "エンジェルガチョを購入したのですが100ダイヤもらえませんでした"
    
    print("\n第一次生成（无缓存）:")
    result1 = generator.generate_response(test_question, question_type="充值问题")
    print(f"成功: {result1['success']}, 缓存: {result1.get('cached', False)}")
    
    print("\n第二次生成（有缓存）:")
    result2 = generator.generate_response(test_question, question_type="充值问题")
    print(f"成功: {result2['success']}, 缓存: {result2.get('cached', False)}")
    
    # 统计
    print("\n" + "="*80)
    print("📊 统计信息")
    print("="*80)
    stats = generator.get_stats()
    print(f"缓存条目: {stats['cache'].get('total_entries', 0)}")
    print(f"缓存命中: {stats['cache'].get('total_hits', 0)}")
    print(f"API调用: {stats['performance']['api_calls']}")
    print(f"缓存命中率: {stats['performance']['cache_hit_rate']:.1%}")
