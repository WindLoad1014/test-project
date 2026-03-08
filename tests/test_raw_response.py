"""测试API原始返回"""
import requests
import json

BASE_URL = "http://localhost:5000"

# 测试数据
test_email = {
    "sender": "test@example.com",
    "subject": "充值未到账",
    "content": "お問い合わせ：先ほど課金しましたが、ダイヤが反映されていません。",
    "auto_send": False,
    "use_llm": False
}

print("="*60)
print("🔍 测试API原始返回")
print("="*60)

try:
    response = requests.post(
        f"{BASE_URL}/api/email/auto-process",
        json=test_email,
        timeout=30
    )
    
    print(f"\n状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    # 原始文本
    raw_text = response.text
    print(f"\n原始响应文本 (前500字符):")
    print(raw_text[:500])
    
    # 解析为JSON
    data = response.json()
    print(f"\n\n解析后的数据类型: {type(data)}")
    
    if isinstance(data, dict):
        analysis = data.get('analysis', {})
        print(f"analysis 类型: {type(analysis)}")
        
        if isinstance(analysis, dict):
            suggestions = analysis.get('suggestions')
            print(f"suggestions 类型: {type(suggestions)}")
            print(f"suggestions 值: {suggestions}")
        else:
            print(f"⚠️ analysis 不是字典: {analysis}")
    else:
        print(f"⚠️ 返回的不是字典: {data}")
        
except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()
