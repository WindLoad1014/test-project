"""测试LLM配置"""
import sys
sys.path.append('backend')

from llm_generator import LLMGenerator

g = LLMGenerator()
print('API Key:', g.api_key[:30] + '...' if g.api_key else 'None')
print('Base URL:', g.base_url)
print('Model:', g.model)
