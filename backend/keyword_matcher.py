"""
关键词匹配检索模块
使用简单的关键词匹配实现快速检索，作为MVP方案
"""
import json
import re
from pathlib import Path
from typing import List, Dict
from collections import Counter
try:
    from config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
    TOP_K = Config.TOP_K
except ImportError:
    from backend.config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
    TOP_K = Config.TOP_K


class KeywordMatcher:
    """关键词匹配器：基于关键词重叠度进行匹配"""
    
    def __init__(self):
        self.qa_pairs = []
        self.keyword_index = {}  # 关键词 -> 问答对索引列表
        
    def load_qa_pairs(self) -> List[Dict]:
        """加载处理后的问答对"""
        json_path = PROCESSED_DATA_PATH / "qa_pairs.json"
        print(f"📂 加载问答对: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.qa_pairs = json.load(f)
        
        print(f"✅ 加载完成: {len(self.qa_pairs)} 个问答对")
        return self.qa_pairs
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单的日文分词）"""
        if not text:
            return []
        
        # 转换为小写并清理
        text = text.lower()
        
        # 提取日文词汇（2-6个字符的词）
        words = []
        for i in range(len(text) - 1):
            for length in range(2, min(7, len(text) - i + 1)):
                word = text[i:i+length]
                # 过滤掉纯数字、纯符号
                if any(c.isalpha() for c in word):
                    words.append(word)
        
        # 统计词频，返回高频词
        word_counts = Counter(words)
        # 返回出现2次以上的词，或所有词（如果太少）
        keywords = [w for w, c in word_counts.most_common(20) if c >= 2]
        if len(keywords) < 5:
            keywords = [w for w, c in word_counts.most_common(10)]
        
        return keywords
    
    def build_index(self):
        """构建关键词索引"""
        if not self.qa_pairs:
            self.load_qa_pairs()
        
        print("🔨 构建关键词索引...")
        
        self.keyword_index = {}
        
        for idx, qa in enumerate(self.qa_pairs):
            question = qa.get('question_raw', '')
            keywords = self.extract_keywords(question)
            
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(idx)
        
        print(f"✅ 索引构建完成")
        print(f"   问答对数: {len(self.qa_pairs)}")
        print(f"   关键词数: {len(self.keyword_index)}")
    
    def search(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """搜索相似问答对"""
        if not self.keyword_index:
            self.build_index()
        
        # 提取查询关键词
        query_keywords = self.extract_keywords(query)
        
        # 统计匹配的问答对
        match_scores = {}
        
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for idx in self.keyword_index[keyword]:
                    match_scores[idx] = match_scores.get(idx, 0) + 1
        
        # 计算相似度分数（归一化）
        results = []
        for idx, score in match_scores.items():
            qa = self.qa_pairs[idx]
            question_keywords = self.extract_keywords(qa.get('question_raw', ''))
            
            # Jaccard相似度
            if question_keywords:
                union = len(set(query_keywords) | set(question_keywords))
                similarity = score / union if union > 0 else 0
            else:
                similarity = 0
            
            result = {
                'id': idx,
                'similarity': similarity,
                'match_count': score,
                'question': qa.get('question_raw', ''),
                'answer': qa.get('answer', ''),
                'question_type': qa.get('question_type', ''),
                'question_type_cn': qa.get('question_type_cn', ''),
                'platform': qa.get('platform', ''),
                'mail_id': qa.get('mail_id', 0)
            }
            results.append(result)
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.qa_pairs:
            self.load_qa_pairs()
        
        # 统计问题类型
        type_counts = {}
        for qa in self.qa_pairs:
            qtype = qa.get('question_type_cn', '其他')
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        return {
            'total_qa_pairs': len(self.qa_pairs),
            'total_keywords': len(self.keyword_index),
            'question_types': type_counts
        }


def main():
    """主函数：构建索引并测试"""
    matcher = KeywordMatcher()
    
    # 构建索引
    matcher.build_index()
    
    # 打印统计
    stats = matcher.get_stats()
    print("\n" + "="*60)
    print("📊 关键词索引统计")
    print("="*60)
    print(f"总问答对数: {stats['total_qa_pairs']}")
    print(f"总关键词数: {stats['total_keywords']}")
    print(f"\n问题类型分布:")
    for qtype, count in sorted(stats['question_types'].items(), key=lambda x: -x[1]):
        print(f"  - {qtype}: {count}")
    
    # 测试搜索
    print("\n" + "="*60)
    print("🔍 测试搜索")
    print("="*60)
    
    test_queries = [
        "イベントのアイテムが出ない",
        "ダイヤが増えない",
        "データが消えた",
        "ガラス瓶が出ない"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = matcher.search(query, top_k=2)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  【{i}】相似度: {result['similarity']:.3f} | 类型: {result['question_type_cn']}")
                print(f"      问题: {result['question'][:50]}...")
        else:
            print("  ⚠️ 未找到匹配结果")


if __name__ == "__main__":
    main()
