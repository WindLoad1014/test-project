"""
API集成测试用例
测试客服系统自动回复功能
"""
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:5000"


def test_health_check():
    """测试健康检查接口"""
    print("\n" + "="*60)
    print("🏥 测试1: 健康检查")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_stats():
    """测试统计信息接口"""
    print("\n" + "="*60)
    print("📊 测试2: 统计信息")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ 统计信息获取成功")
            return True
        else:
            print("❌ 统计信息获取失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_email_list():
    """测试邮件列表接口"""
    print("\n" + "="*60)
    print("📧 测试3: 邮件列表")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/emails",
            params={"page": 1, "per_page": 5},
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print(f"总邮件数: {data.get('total', 0)}")
            print(f"当前页邮件数: {len(data.get('emails', []))}")
            if data.get('emails'):
                print(f"第一条邮件主题: {data['emails'][0].get('subject', 'N/A')}")
            print("✅ 邮件列表获取成功")
            return True
        else:
            print("❌ 邮件列表获取失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_receive_email():
    """测试接收邮件接口"""
    print("\n" + "="*60)
    print("📨 测试4: 接收邮件")
    print("="*60)
    
    test_email = {
        "sender": "test_player@example.com",
        "subject": "充值未到账",
        "content": """
お問い合わせ
アカウントID : TEST123456
プレイヤー名 : TestPlayer
アプリバージョン : 1.2.0
ご利用のOSバージョン : iOS 16.0
ご利用端末名 : iPhone14
お問い合わせ内容の種類 : 課金について
ご利用環境 : App Store
問題が発生した日時 : 2024-03-15 10:30
メールアドレス : test@example.com
お問い合わせ内容：先ほど課金しましたが、ダイヤが反映されていません。
        """,
        "platform": "App Store",
        "app_version": "1.2.0",
        "device": "iPhone14",
        "account_id": "TEST123456",
        "player_name": "TestPlayer"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/email/receive",
            json=test_email,
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            print(f"✅ 邮件接收成功，ID: {data.get('email_id')}")
            return data.get('email_id')
        else:
            print("❌ 邮件接收失败")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_analyze_email(email_id: int):
    """测试邮件分析接口"""
    print("\n" + "="*60)
    print("🔍 测试5: 邮件分析")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/email/{email_id}/analyze",
            timeout=15
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            analysis = data.get('analysis', {})
            print(f"✅ 分析成功")
            print(f"   问题类型: {analysis.get('question_type')}")
            print(f"   紧急度: {analysis.get('urgency')}")
            print(f"   情感: {analysis.get('sentiment')}")
            return True
        else:
            print("❌ 分析失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_generate_reply(email_id: int):
    """测试生成回复接口"""
    print("\n" + "="*60)
    print("✍️ 测试6: 生成回复")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/email/{email_id}/generate-reply",
            json={"use_llm": False},  # 使用模板回复，不调用LLM
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            reply = data.get('reply', {})
            print(f"✅ 回复生成成功")
            print(f"   生成方式: {reply.get('model')}")
            print(f"   置信度: {reply.get('confidence')}")
            print(f"   回复内容预览: {reply.get('content', '')[:100]}...")
            return data.get('reply_id')
        else:
            print("❌ 回复生成失败")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_auto_process():
    """测试自动处理接口（一键处理）"""
    print("\n" + "="*60)
    print("🤖 测试7: 自动处理（一键处理）")
    print("="*60)
    
    test_email = {
        "sender": "auto_test@example.com",
        "subject": "账号无法登录",
        "content": """
お問い合わせ
アカウントID : AUTO789
プレイヤー名 : AutoTest
アプリバージョン : 1.1.5
ご利用のOSバージョン : Android 13
ご利用端末名 : Galaxy S23
お問い合わせ内容の種類 : アカウントについて
ご利用環境 : Google Play
問題が発生した日時 : 2024-03-15 14:00
メールアドレス : auto@example.com
お問い合わせ内容：パスワードを忘れてログインできません。助けてください。
        """,
        "platform": "Google Play",
        "app_version": "1.1.5",
        "device": "Galaxy S23",
        "account_id": "AUTO789",
        "player_name": "AutoTest",
        "auto_send": False,  # 不自动发送，仅生成回复
        "use_llm": False     # 使用模板回复
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/email/auto-process",
            json=test_email,
            timeout=20
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            print(f"✅ 自动处理成功")
            print(f"   邮件ID: {data.get('email_id')}")
            print(f"   回复ID: {data.get('reply_id')}")
            print(f"   是否自动发送: {data.get('auto_sent')}")
            
            analysis = data.get('analysis', {})
            print(f"   分析结果:")
            print(f"     - 问题类型: {analysis.get('question_type')}")
            print(f"     - 紧急度: {analysis.get('urgency')}")
            print(f"     - 情感: {analysis.get('sentiment')}")
            
            reply = data.get('reply', {})
            print(f"   回复预览: {reply.get('content', '')[:100]}...")
            return True
        else:
            print("❌ 自动处理失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_auto_process_with_llm():
    """测试自动处理接口（使用LLM生成回复）"""
    print("\n" + "="*60)
    print("🤖 测试9: 自动处理（使用LLM生成回复）")
    print("="*60)
    
    test_email = {
        "sender": "llm_test@example.com",
        "subject": "充值未到账",
        "content": """
お問い合わせ
アカウントID : LLM123
プレイヤー名 : LLMTest
アプリバージョン : 1.2.0
ご利用のOSバージョン : iOS 16.0
ご利用端末名 : iPhone14
お問い合わせ内容の種類 : 課金について
ご利用環境 : App Store
問題が発生した日時 : 2024-03-15 10:30
メールアドレス : llm@example.com
お問い合わせ内容：先ほど課金しましたが、ダイヤが反映されていません。どうすればいいですか？
        """,
        "platform": "App Store",
        "app_version": "1.2.0",
        "device": "iPhone14",
        "account_id": "LLM123",
        "player_name": "LLMTest",
        "auto_send": False,  # 不自动发送，仅生成回复
        "use_llm": True      # 使用LLM生成回复
    }
    
    try:
        print("⏳ 正在调用LLM生成回复，请稍候...")
        response = requests.post(
            f"{BASE_URL}/api/email/auto-process",
            json=test_email,
            timeout=60  # LLM调用可能需要更长时间
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print(f"✅ 自动处理成功")
            print(f"   邮件ID: {data.get('email_id')}")
            print(f"   回复ID: {data.get('reply_id')}")
            print(f"   是否自动发送: {data.get('auto_sent')}")
            
            analysis = data.get('analysis', {})
            print(f"\n📊 分析结果:")
            print(f"   - 问题类型: {analysis.get('question_type')}")
            print(f"   - 紧急度: {analysis.get('urgency')}")
            print(f"   - 情感: {analysis.get('sentiment')}")
            
            reply = data.get('reply', {})
            model = reply.get('model', 'unknown')
            content = reply.get('content', '')
            
            print(f"\n📝 回复信息:")
            print(f"   - 生成方式: {model}")
            print(f"   - 置信度: {reply.get('confidence')}")
            print(f"   - 是否回退: {reply.get('is_fallback', False)}")
            
            print(f"\n" + "="*60)
            print("📧 LLM生成的回复内容:")
            print("="*60)
            print(content)
            print("="*60)
            
            if model == 'llm':
                print("\n✅ 成功使用LLM生成回复！")
            else:
                print(f"\n⚠️ 未使用LLM，实际使用: {model}")
            
            return True
        else:
            print("❌ 自动处理失败")
            print(f"错误信息: {data.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_knowledge_base_search():
    """测试知识库搜索接口"""
    print("\n" + "="*60)
    print("📚 测试8: 知识库搜索")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/knowledge-base/search",
            json={"query": "充值", "top_k": 5},
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            results = data.get('results', [])
            print(f"搜索结果数: {len(results)}")
            if results:
                print(f"第一条结果:")
                print(f"  问题: {results[0].get('question', 'N/A')[:50]}...")
                print(f"  相似度: {results[0].get('similarity', 0):.2f}")
            print("✅ 知识库搜索成功")
            return True
        else:
            print(f"❌ 知识库搜索失败: {data.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 客服系统API集成测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}")
    
    results = []
    
    # 基础测试
    results.append(("健康检查", test_health_check()))
    results.append(("统计信息", test_stats()))
    results.append(("邮件列表", test_email_list()))
    results.append(("知识库搜索", test_knowledge_base_search()))
    
    # 流程测试
    email_id = test_receive_email()
    if email_id:
        results.append(("接收邮件", True))
        results.append(("邮件分析", test_analyze_email(email_id)))
        reply_id = test_generate_reply(email_id)
        results.append(("生成回复", reply_id is not None))
    else:
        results.append(("接收邮件", False))
        results.append(("邮件分析", False))
        results.append(("生成回复", False))
    
    # 自动处理测试
    results.append(("自动处理", test_auto_process()))
    
    # LLM回复测试
    results.append(("LLM回复", test_auto_process_with_llm()))
    
    # 测试总结
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("-"*60)
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查日志")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
