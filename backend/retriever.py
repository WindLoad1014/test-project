"""
统一检索接口模块
提供标准化的检索接口，支持多种检索策略
"""
import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path
from difflib import SequenceMatcher

try:
    from config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
    TOP_K = Config.TOP_K
except ImportError:
    from backend.config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
    TOP_K = Config.TOP_K


class BaseRetriever(ABC):
    """检索器基类"""
    
    @abstractmethod
    def search(self, query: str, top_k: int = TOP_K, **kwargs) -> List[Dict]:
        """
        检索接口
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    def build_index(self, force_rebuild: bool = False):
        """构建索引"""
        pass


class KeywordRetriever(BaseRetriever):
    """关键词检索器"""
    
    def __init__(self):
        self.qa_pairs = []
        self.keyword_index = {}
        
    def load_qa_pairs(self) -> List[Dict]:
        """加载问答对"""
        json_path = PROCESSED_DATA_PATH / "qa_pairs.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            self.qa_pairs = json.load(f)
        return self.qa_pairs
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        # 日文分词：按字符和常见词分割
        words = []
        # 提取2-4字的词组
        for i in range(len(text)):
            for j in range(2, min(5, len(text) - i + 1)):
                word = text[i:i+j]
                if len(word) >= 2:
                    words.append(word)
        return list(set(words))
    
    def build_index(self, force_rebuild: bool = False):
        """构建关键词索引"""
        if not self.qa_pairs:
            self.load_qa_pairs()
        
        print(f"🔨 构建关键词索引...")
        self.keyword_index = {}
        
        for idx, qa in enumerate(self.qa_pairs):
            question = qa.get('question_raw', '')
            answer = qa.get('answer', '')
            
            # 提取关键词
            keywords = self.extract_keywords(question)
            keywords.extend(self.extract_keywords(answer))
            
            # 建立倒排索引
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(idx)
        
        print(f"✅ 索引构建完成: {len(self.qa_pairs)} 个问答对, {len(self.keyword_index)} 个关键词")
    
    def fuzzy_match(self, query: str, text: str) -> float:
        """
        计算模糊匹配相似度
        
        Args:
            query: 查询文本
            text: 待匹配文本
            
        Returns:
            相似度分数 (0-1)
        """
        if not query or not text:
            return 0.0
        
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, query.lower(), text.lower()).ratio()
        
        # 额外奖励：如果查询是文本的子串，提高分数
        if query.lower() in text.lower():
            similarity = min(similarity + 0.2, 1.0)
        
        # 额外奖励：如果文本包含查询中的关键词
        query_keywords = self.extract_keywords(query)
        text_keywords = self.extract_keywords(text)
        if query_keywords and text_keywords:
            common = set(query_keywords) & set(text_keywords)
            if common:
                keyword_ratio = len(common) / len(query_keywords)
                similarity = min(similarity + keyword_ratio * 0.1, 1.0)
        
        return similarity
    
    def search(self, query: str, top_k: int = TOP_K, **kwargs) -> List[Dict]:
        """
        关键词检索（支持模糊搜索）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            question_type: 可选，按问题类型过滤
            fuzzy: 是否启用模糊搜索，默认True
            
        Returns:
            检索结果列表，包含相似度分数
        """
        if not self.qa_pairs:
            self.build_index()
        
        question_type = kwargs.get('question_type')
        use_fuzzy = kwargs.get('fuzzy', True)  # 默认启用模糊搜索
        
        # 提取查询关键词
        query_keywords = self.extract_keywords(query)
        
        # 计算匹配分数
        scores = {}
        
        if query_keywords:
            # 关键词匹配
            for keyword in query_keywords:
                if keyword in self.keyword_index:
                    for idx in self.keyword_index[keyword]:
                        scores[idx] = scores.get(idx, 0) + 1
            
            # 归一化分数
            for idx in scores:
                qa = self.qa_pairs[idx]
                question_keywords = self.extract_keywords(qa.get('question_raw', ''))
                if question_keywords:
                    scores[idx] /= len(question_keywords)
        
        # 模糊搜索（当关键词匹配结果不足或启用模糊搜索时）
        if use_fuzzy:
            # 对所有问答对计算模糊相似度
            for idx, qa in enumerate(self.qa_pairs):
                question = qa.get('question_raw', '')
                answer = qa.get('answer', '')
                
                # 计算与问题和答案的模糊相似度
                question_sim = self.fuzzy_match(query, question)
                answer_sim = self.fuzzy_match(query, answer[:200])  # 只比较答案前200字符
                
                # 取最大相似度
                fuzzy_score = max(question_sim, answer_sim * 0.5)  # 答案相似度权重降低
                
                # 合并分数（如果已有关键词匹配分数）
                if idx in scores:
                    # 加权合并：关键词匹配占60%，模糊匹配占40%
                    scores[idx] = scores[idx] * 0.6 + fuzzy_score * 0.4
                else:
                    # 只有模糊匹配分数
                    if fuzzy_score > 0.05:  # 降低最低阈值以提高召回率
                        scores[idx] = fuzzy_score
        
        # 排序并获取Top-K
        sorted_results = sorted(scores.items(), key=lambda x: -x[1])
        
        results = []
        for idx, score in sorted_results[:top_k]:
            qa = self.qa_pairs[idx]
            
            # 类型过滤
            if question_type and qa.get('question_type_cn') != question_type:
                continue
            
            result = {
                'id': idx,
                'similarity': min(score, 1.0),  # 限制最大为1.0
                'question': qa.get('question_raw', ''),
                'answer': qa.get('answer', ''),
                'question_type': qa.get('question_type', ''),
                'question_type_cn': qa.get('question_type_cn', ''),
                'platform': qa.get('platform', ''),
                'mail_id': qa.get('mail_id', 0)
            }
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.qa_pairs:
            self.load_qa_pairs()
        
        type_counts = {}
        for qa in self.qa_pairs:
            qtype = qa.get('question_type_cn', '未知')
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        return {
            'total_qa_pairs': len(self.qa_pairs),
            'total_keywords': len(self.keyword_index),
            'question_types': type_counts
        }


class RetrieverFactory:
    """检索器工厂"""
    
    _instances = {}
    
    @classmethod
    def get_retriever(cls, retriever_type: str = 'keyword') -> BaseRetriever:
        """
        获取检索器实例（单例模式）
        
        Args:
            retriever_type: 检索器类型 ('keyword')
            
        Returns:
            检索器实例
        """
        if retriever_type not in cls._instances:
            if retriever_type == 'keyword':
                retriever = KeywordRetriever()
                retriever.build_index()
                cls._instances[retriever_type] = retriever
            else:
                raise ValueError(f"不支持的检索器类型: {retriever_type}")
        
        return cls._instances[retriever_type]
    
    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._instances.clear()


# 便捷函数
def search_similar_cases(query: str, top_k: int = TOP_K, 
                        question_type: str = None) -> List[Dict]:
    """
    便捷检索函数
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        question_type: 问题类型过滤
        
    Returns:
        相似案例列表
    """
    retriever = RetrieverFactory.get_retriever('keyword')
    return retriever.search(query, top_k, question_type=question_type)


if __name__ == "__main__":
    # 测试
    print("="*80)
    print("🔍 统一检索接口测试")
    print("="*80)
    
    # 测试关键词检索
    retriever = RetrieverFactory.get_retriever('keyword')
    
    test_queries = [
        "エンジェルガチョを購入したのですが100ダイヤもらえない",
        "イベントのアイテムが図鑑に反映されない",
        "データが消えた"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = retriever.search(query, top_k=3)
        print(f"找到 {len(results)} 个相似案例:")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] 相似度: {r['similarity']:.1%} | {r['question'][:40]}...")
    
    # 统计信息
    print("\n" + "="*80)
    print("📊 统计信息")
    print("="*80)
    stats = retriever.get_stats()
    print(f"问答对总数: {stats['total_qa_pairs']}")
    print(f"关键词总数: {stats['total_keywords']}")
    print(f"问题类型分布:")
    for qtype, count in sorted(stats['question_types'].items(), key=lambda x: -x[1])[:5]:
        print(f"  - {qtype}: {count}")
