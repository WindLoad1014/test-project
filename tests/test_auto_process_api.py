"""测试自动处理API"""
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
アプリバージョン : 1.2.0
ご利用のOSバージョン : iOS 16.0
ご利用端末名 : iPhone14
お問い合わせ内容の種類 : 課金について
ご利用環境 : App Store
問題が発生した日時 : 2024-03-15 10:30
メールアドレス : test@example.com
お問い合わせ内容：先ほど課金しましたが、ダイヤが反映されていません。どうすればいいですか？
    """,
    "platform": "App Store",
    "app_version": "1.2.0",
    "device": "iPhone14",
    "account_id": "TEST123",
    "player_name": "TestPlayer",
    "auto_send": False,
    "use_llm": True
}

print("="*60)
print("🤖 测试自动处理API（使用LLM）")
print("="*60)

try:
    print("\n⏳ 发送请求...")
    response = requests.post(
        f"{BASE_URL}/api/email/auto-process",
        json=test_email,
        timeout=60
    )
    
    print(f"状态码: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200 and data.get('success'):
        print("\n✅ 自动处理成功")
        print(f"邮件ID: {data.get('email_id')}")
        print(f"回复ID: {data.get('reply_id')}")
        print(f"是否自动发送: {data.get('auto_sent')}")
        
        analysis = data.get('analysis', {})
        print(f"\n📊 分析结果:")
        print(f"  - 问题类型: {analysis.get('question_type')}")
        print(f"  - 紧急度: {analysis.get('urgency')}")
        print(f"  - 情感: {analysis.get('sentiment')}")
        
        reply = data.get('reply', {})
        print(f"\n📝 回复信息:")
        print(f"  - 生成方式: {reply.get('model')}")
        print(f"  - 置信度: {reply.get('confidence')}")
        print(f"  - 是否回退: {reply.get('is_fallback', False)}")
        
        print(f"\n" + "="*60)
        print("📧 生成的回复内容:")
        print("="*60)
        print(reply.get('content', '无内容'))
        print("="*60)
        
        if 'llm' in reply.get('model', '').lower() or reply.get('model') == 'qwen3.5-plus':
            print("\n✅ 成功使用LLM生成回复！")
        else:
            print(f"\n⚠️ 未使用LLM，实际使用: {reply.get('model')}")
            if reply.get('is_fallback'):
                print("   原因: 使用了降级方案")
    else:
        print("\n❌ 自动处理失败")
        print(f"错误信息: {data.get('error', '未知错误')}")
        
except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()
