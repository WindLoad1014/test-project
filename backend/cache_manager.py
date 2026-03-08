"""
缓存管理模块
提供LLM生成结果缓存，降低API调用成本
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
try:
    from config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
except ImportError:
    from backend.config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    query: str
    response: str
    model: str
    timestamp: float
    hit_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        return cls(**data)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_file: str = "llm_cache.json", max_size: int = 1000):
        self.cache_dir = PROCESSED_DATA_PATH
        self.cache_file = self.cache_dir / cache_file
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self._load_cache()
    
    def _generate_key(self, query: str, model: str, **kwargs) -> str:
        """生成缓存键"""
        # 规范化查询文本
        normalized = query.strip().lower().replace(" ", "").replace("　", "")
        content = f"{normalized}:{model}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _load_cache(self):
        """从文件加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        self.cache[key] = CacheEntry.from_dict(entry_data)
                print(f"📂 加载缓存: {len(self.cache)} 条记录")
            except Exception as e:
                print(f"⚠️ 缓存加载失败: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        try:
            data = {k: v.to_dict() for k, v in self.cache.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")
    
    def get(self, query: str, model: str, **kwargs) -> Optional[str]:
        """
        获取缓存
        
        Args:
            query: 查询文本
            model: 模型名称
            **kwargs: 其他参数
            
        Returns:
            缓存的响应或None
        """
        key = self._generate_key(query, model, **kwargs)
        
        if key in self.cache:
            entry = self.cache[key]
            entry.hit_count += 1
            entry.timestamp = time.time()  # 更新访问时间
            print(f"💾 缓存命中 (命中次数: {entry.hit_count})")
            return entry.response
        
        return None
    
    def set(self, query: str, response: str, model: str, **kwargs):
        """
        设置缓存
        
        Args:
            query: 查询文本
            response: 响应内容
            model: 模型名称
            **kwargs: 其他参数
        """
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # LRU淘汰：移除最久未访问的
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]
            print(f"🗑️ 缓存淘汰: {oldest_key[:8]}...")
        
        key = self._generate_key(query, model, **kwargs)
        
        self.cache[key] = CacheEntry(
            key=key,
            query=query[:100],  # 只保存前100字符
            response=response,
            model=model,
            timestamp=time.time(),
            hit_count=0
        )
        
        # 异步保存（可以优化为定时保存）
        self._save_cache()
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        print("🗑️ 缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self.cache:
            return {
                'total_entries': 0,
                'total_hits': 0,
                'hit_rate': 0.0
            }
        
        total_hits = sum(e.hit_count for e in self.cache.values())
        
        return {
            'total_entries': len(self.cache),
            'total_hits': total_hits,
            'hit_rate': total_hits / len(self.cache) if self.cache else 0.0,
            'cache_file': str(self.cache_file),
            'max_size': self.max_size
        }
    
    def get_popular_queries(self, top_k: int = 10) -> list:
        """获取热门查询"""
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda e: e.hit_count,
            reverse=True
        )
        return [
            {
                'query': e.query,
                'hits': e.hit_count,
                'model': e.model
            }
            for e in sorted_entries[:top_k]
        ]


# 全局缓存实例
_cache_instance: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance


if __name__ == "__main__":
    # 测试
    print("="*80)
    print("💾 缓存管理器测试")
    print("="*80)
    
    cache = CacheManager()
    
    # 测试设置缓存
    test_queries = [
        ("エンジェルガチョを購入したのですがダイヤがもらえない", "いつもご利用ありがとうございます..."),
        ("イベントのアイテムが反映されない", "ご迷惑をおかけしております..."),
    ]
    
    print("\n📝 设置缓存...")
    for query, response in test_queries:
        cache.set(query, response, model="qwen3.5-plus")
        print(f"  ✓ 已缓存: {query[:30]}...")
    
    # 测试获取缓存
    print("\n🔍 获取缓存...")
    for query, _ in test_queries:
        result = cache.get(query, model="qwen3.5-plus")
        if result:
            print(f"  ✓ 命中: {query[:30]}...")
        else:
            print(f"  ✗ 未命中: {query[:30]}...")
    
    # 测试未缓存的查询
    print("\n🔍 测试未缓存查询...")
    result = cache.get("存在しないクエリ", model="qwen3.5-plus")
    print(f"  {'✓ 命中' if result else '✗ 未命中'}: 存在しないクエリ")
    
    # 统计信息
    print("\n" + "="*80)
    print("📊 缓存统计")
    print("="*80)
    stats = cache.get_stats()
    print(f"缓存条目数: {stats['total_entries']}")
    print(f"总命中次数: {stats['total_hits']}")
    print(f"平均命中率: {stats['hit_rate']:.2f}")
    
    # 热门查询
    print("\n🔥 热门查询:")
    popular = cache.get_popular_queries(top_k=5)
    for i, item in enumerate(popular, 1):
        print(f"  [{i}] {item['query'][:40]}... (命中{item['hits']}次)")
