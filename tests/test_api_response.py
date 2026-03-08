"""测试API返回的数据结构"""
import requests
import json

BASE_URL = "http://localhost:5000"

# 测试数据
test_email = {
    "sender": "test@example.com",
    "subject": "充值未到账",
    "content": """
お問い合わせ
アカウントID : TEST123
プレイヤー名 : TestPlayer
お問い合わせ内容：先ほど課金しましたが、ダイヤが反映されていません。
    """,
    "auto_send": False,
    "use_llm": False  # 不用LLM，更快
}

print("="*60)
print("🔍 测试API返回的数据结构")
print("="*60)

try:
    response = requests.post(
        f"{BASE_URL}/api/email/auto-process",
        json=test_email,
        timeout=30
    )
    
    data = response.json()
    
    if response.status_code == 200 and data.get('success'):
        print("\n✅ API调用成功")
        
        analysis = data.get('analysis', {})
        suggestions = analysis.get('suggestions', [])
        
        print(f"\n📊 analysis 类型检查:")
        print(f"  analysis 类型: {type(analysis)}")
        print(f"  suggestions 类型: {type(suggestions)}")
        print(f"  suggestions 内容: {suggestions}")
        
        if isinstance(suggestions, list):
            print(f"\n✅ suggestions 是列表，包含 {len(suggestions)} 项:")
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")
        elif isinstance(suggestions, str):
            print(f"\n⚠️ suggestions 是字符串！")
            print(f"  内容: {suggestions}")
            print(f"  字符列表: {list(suggestions)}")
        else:
            print(f"\n❌ suggestions 是未知类型: {type(suggestions)}")
    else:
        print(f"\n❌ API调用失败: {data.get('error', '未知错误')}")
        
except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()
