"""测试LLM API调用"""
import sys
sys.path.append('backend')

from llm_generator import LLMGenerator

g = LLMGenerator()

# 测试生成回复
result = g.generate_response(
    player_question="先ほど課金しましたが、ダイヤが反映されていません。",
    similar_cases=[],
    question_type="充值问题",
    use_cache=False  # 不使用缓存，强制调用API
)

print("\n结果:")
print(f"Success: {result['success']}")
print(f"Model: {result.get('model')}")
print(f"Cached: {result.get('cached')}")
if result['success']:
    print(f"\n回复内容:\n{result['response']}")
else:
    print(f"Error: {result.get('error')}")
