"""测试模糊搜索功能"""
import sys
sys.path.append('backend')

from retriever import KeywordRetriever

# 创建检索器
retriever = KeywordRetriever()
retriever.build_index()

print("="*60)
print("🔍 测试模糊搜索功能")
print("="*60)

# 测试查询
test_queries = [
    "充值不到账",  # 关键词匹配
    "充了钱没收到",  # 模糊匹配
    "钻石没到账",  # 模糊匹配
    "bug反馈",  # 关键词匹配
    "游戏卡顿",  # 模糊匹配
]

for query in test_queries:
    print(f"\n查询: {query}")
    print("-"*40)
    
    # 启用模糊搜索
    results_fuzzy = retriever.search(query, top_k=3, fuzzy=True)
    print(f"模糊搜索: 找到 {len(results_fuzzy)} 条结果")
    for i, r in enumerate(results_fuzzy, 1):
        print(f"  {i}. [{r['question_type_cn']}] 相似度: {r['similarity']:.2f}")
        print(f"     问题: {r['question'][:50]}...")
    
    # 禁用模糊搜索
    results_exact = retriever.search(query, top_k=3, fuzzy=False)
    print(f"精确搜索: 找到 {len(results_exact)} 条结果")
    for i, r in enumerate(results_exact, 1):
        print(f"  {i}. [{r['question_type_cn']}] 相似度: {r['similarity']:.2f}")
        print(f"     问题: {r['question'][:50]}...")

print("\n" + "="*60)
print("✅ 测试完成")
