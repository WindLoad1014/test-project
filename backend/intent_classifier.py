"""
意图分类模块
自动识别玩家咨询的问题类型和紧急程度
"""
import json
import re
from typing import Dict, Tuple
from collections import Counter
try:
    from config import Config
    QUESTION_TYPES = Config.QUESTION_TYPES
except ImportError:
    from backend.config import Config
    QUESTION_TYPES = Config.QUESTION_TYPES


class IntentClassifier:
    """意图分类器：识别问题类型和紧急程度"""
    
    def __init__(self):
        # 关键词词典
        self.keywords = {
            "充值问题": {
                "high": ["課金", "購入", "ダイヤ", "支払", "課金", "課金", "課金", "課金", "課金", "課金"],
                "medium": ["アイテム", "購入", "支払", "課金", "課金", "課金", "課金", "課金", "課金", "課金"]
            },
            "BUG反馈": {
                "high": ["消え", "データ", "バグ", "不具合", "クラッシュ", "フリーズ", "エラー"],
                "medium": ["表示", "おかしい", "動かない", "開かない", "入れない"]
            },
            "意见建议": {
                "high": ["要望", "意見", "改善", "追加", "機能", "イベント"],
                "medium": ["難しい", "簡単", "面白い", "つまらない", "飽き"]
            },
            "账号问题": {
                "high": ["アカウント", "ログイン", "パスワード", "認証", "引き継ぎ"],
                "medium": ["ID", "ユーザー", "名前", "変更"]
            }
        }
        
        # 紧急度关键词
        self.urgency_keywords = {
            "high": [
                "至急", "急ぎ", "すぐ", "今すぐ", "早く", "待てない",
                "課金", "お金", "払った", "支払", "返金", "返して",
                "消えた", "データ", "復旧", "戻して"
            ],
            "medium": [
                "困る", "不便", "欲しい", "できない", "助けて",
                "教えて", "知りたい", "確認", "問い合わせ"
            ]
        }
        
        # 情绪关键词
        self.sentiment_keywords = {
            "angry": ["怒", "最悪", "ゴミ", "クソ", "ひどい", "許せない", "詐欺", "ふざけ"],
            "frustrated": ["困る", "不便", "難しい", "わかりにくい", "面倒", "めんどう"],
            "neutral": [],
            "positive": ["楽しい", "好き", "素晴らしい", "最高", "ありがとう", "感謝"]
        }
    
    def classify_question_type(self, text: str, parsed_type: str = "") -> Tuple[str, float]:
        """分类问题类型"""
        text = text.lower()
        
        # 如果解析出的类型有效，直接使用
        if parsed_type and parsed_type in QUESTION_TYPES:
            return QUESTION_TYPES[parsed_type], 0.9
        
        # 关键词匹配
        scores = {}
        for qtype, keywords in self.keywords.items():
            score = 0
            for word in keywords["high"]:
                if word in text:
                    score += 2
            for word in keywords["medium"]:
                if word in text:
                    score += 1
            scores[qtype] = score
        
        # 返回最高分的类型
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            
            # 归一化置信度
            confidence = min(best_score / 5, 1.0) if best_score > 0 else 0
            
            return best_type, confidence
        
        return "其他", 0.0
    
    def classify_urgency(self, text: str, question_type: str = "") -> Tuple[str, float, str]:
        """
        分类紧急程度
        返回: (紧急度, 置信度, 原因)
        """
        text = text.lower()
        score = 0
        reasons = []
        
        # 根据问题类型基础分
        type_urgency = {
            "充值问题": 3,
            "BUG反馈": 2,
            "账号问题": 3,
            "意见建议": 0,
            "其他": 1
        }
        
        base_score = type_urgency.get(question_type, 1)
        score += base_score
        
        if base_score >= 3:
            reasons.append(f"问题类型为{question_type}")
        
        # 关键词匹配
        for word in self.urgency_keywords["high"]:
            if word in text:
                score += 2
                reasons.append(f"包含紧急关键词'{word}'")
                break
        
        for word in self.urgency_keywords["medium"]:
            if word in text:
                score += 1
                break
        
        # 判断紧急度等级
        if score >= 5:
            return "high", min(score / 8, 1.0), "; ".join(reasons) if reasons else "综合判断"
        elif score >= 3:
            return "medium", min(score / 5, 1.0), "; ".join(reasons) if reasons else "综合判断"
        else:
            return "low", 0.5, "常规咨询"
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """分析情绪"""
        text = text.lower()
        
        scores = {}
        for sentiment, keywords in self.sentiment_keywords.items():
            score = sum(1 for word in keywords if word in text)
            scores[sentiment] = score
        
        # 返回最高分的情绪
        if max(scores.values()) > 0:
            best_sentiment = max(scores, key=scores.get)
            return best_sentiment, min(scores[best_sentiment] / 2, 1.0)
        
        return "neutral", 0.5
    
    def classify(self, text: str, parsed_type: str = "") -> Dict:
        """
        完整分类
        返回包含问题类型、紧急度、情绪等的完整分析
        """
        # 问题类型
        qtype, qtype_conf = self.classify_question_type(text, parsed_type)
        
        # 紧急度
        urgency, urgency_conf, urgency_reason = self.classify_urgency(text, qtype)
        
        # 情绪
        sentiment, sentiment_conf = self.analyze_sentiment(text)
        
        # 生成建议
        suggestions = self.generate_suggestions(qtype, urgency, sentiment)
        
        return {
            "question_type": qtype,
            "question_type_confidence": round(qtype_conf, 2),
            "urgency": urgency,
            "urgency_confidence": round(urgency_conf, 2),
            "urgency_reason": urgency_reason,
            "sentiment": sentiment,
            "sentiment_confidence": round(sentiment_conf, 2),
            "suggestions": suggestions
        }
    
    def generate_suggestions(self, question_type: str, urgency: str, sentiment: str) -> list:
        """生成处理建议"""
        suggestions = []
        
        # 基于紧急度的建议
        if urgency == "high":
            suggestions.append("🔴 高优先级：建议30分钟内回复")
            suggestions.append("🔴 需要立即调查并给出明确时间表")
        elif urgency == "medium":
            suggestions.append("🟡 中优先级：建议2小时内回复")
            suggestions.append("🟡 需要确认问题并给出初步方案")
        else:
            suggestions.append("🟢 低优先级：建议24小时内回复")
            suggestions.append("🟢 可按标准流程处理")
        
        # 基于问题类型的建议
        type_actions = {
            "充值问题": ["💰 核实充值记录", "💰 检查钻石发放状态", "💰 必要时联系支付平台"],
            "BUG反馈": ["🐛 收集设备信息", "🐛 记录复现步骤", "🐛 转开发团队调查"],
            "意见建议": ["💡 记录反馈内容", "💡 转达给产品团队", "💡 感谢玩家支持"],
            "账号问题": ["👤 核实账号信息", "👤 检查登录日志", "👤 必要时人工介入"]
        }
        
        if question_type in type_actions:
            suggestions.extend(type_actions[question_type])
        
        # 基于情绪的建议
        if sentiment == "angry":
            suggestions.append("😠 玩家情绪愤怒：需要特别安抚，语气要更加诚恳")
        elif sentiment == "frustrated":
            suggestions.append("😤 玩家感到困扰：需要详细解释，提供明确解决方案")
        
        return suggestions
    
    def batch_classify(self, texts: list) -> list:
        """批量分类"""
        results = []
        for text in texts:
            result = self.classify(text)
            results.append(result)
        return results


def test_classifier():
    """测试分类器"""
    print("="*80)
    print("🎯 意图分类器测试")
    print("="*80)
    
    classifier = IntentClassifier()
    
    test_cases = [
        {
            "text": "エンジェルガチョを購入したのですが100ダイヤもらえず、至急対応してください！",
            "parsed_type": "アイテム購入時に問題が発生した"
        },
        {
            "text": "前にプレイしていたデータが消えた、どうしてくれるんだ！",
            "parsed_type": "不具合について"
        },
        {
            "text": "新しいイベントの排出率を上げてほしいです",
            "parsed_type": "ご意見?ご要望"
        },
        {
            "text": "アカウントにログインできなくなりました",
            "parsed_type": "アカウントについて"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试案例 {i}")
        print(f"{'='*80}")
        print(f"文本: {case['text'][:60]}...")
        print(f"解析类型: {case['parsed_type']}")
        
        result = classifier.classify(case['text'], case['parsed_type'])
        
        print(f"\n📊 分类结果:")
        print(f"   问题类型: {result['question_type']} (置信度: {result['question_type_confidence']})")
        print(f"   紧急程度: {result['urgency']} (置信度: {result['urgency_confidence']})")
        print(f"   紧急原因: {result['urgency_reason']}")
        print(f"   情绪: {result['sentiment']} (置信度: {result['sentiment_confidence']})")
        
        print(f"\n💡 处理建议:")
        for suggestion in result['suggestions']:
            print(f"   {suggestion}")


if __name__ == "__main__":
    test_classifier()
