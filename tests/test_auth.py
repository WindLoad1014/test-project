"""
登录功能测试
"""
import requests
import json

BASE_URL = "http://localhost:5000"


def test_login_success():
    """测试正常登录"""
    print("\n" + "="*60)
    print("🔐 测试1: 正常登录")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            print("✅ 登录成功")
            print(f"   Token: {data['token'][:30]}...")
            print(f"   用户名: {data['user']['username']}")
            print(f"   角色: {data['user']['role']}")
            return data['token']
        else:
            print("❌ 登录失败")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_login_wrong_password():
    """测试错误密码"""
    print("\n" + "="*60)
    print("🔐 测试2: 错误密码")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 401:
            print("✅ 正确拒绝错误密码")
            return True
        else:
            print("❌ 应该返回401")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_get_current_user(token):
    """测试获取当前用户信息"""
    print("\n" + "="*60)
    print("🔐 测试3: 获取当前用户信息")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            print("✅ 获取用户信息成功")
            print(f"   用户名: {data['user']['username']}")
            return True
        else:
            print("❌ 获取用户信息失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_access_protected_without_token():
    """测试未登录访问受保护接口"""
    print("\n" + "="*60)
    print("🔐 测试4: 未登录访问受保护接口")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 401:
            print("✅ 正确拒绝未授权访问")
            return True
        else:
            print("❌ 应该返回401")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_logout(token):
    """测试登出"""
    print("\n" + "="*60)
    print("🔐 测试5: 登出")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get('success'):
            print("✅ 登出成功")
            return True
        else:
            print("❌ 登出失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔐 登录功能测试")
    print("="*60)
    
    results = []
    
    # 测试1: 正常登录
    token = test_login_success()
    results.append(("正常登录", token is not None))
    
    # 测试2: 错误密码
    results.append(("错误密码", test_login_wrong_password()))
    
    # 测试3: 获取当前用户信息（需要token）
    if token:
        results.append(("获取用户信息", test_get_current_user(token)))
    else:
        results.append(("获取用户信息", False))
    
    # 测试4: 未登录访问受保护接口
    results.append(("未授权访问", test_access_protected_without_token()))
    
    # 测试5: 登出
    if token:
        results.append(("登出", test_logout(token)))
    else:
        results.append(("登出", False))
    
    # 测试总结
    print("\n" + "="*60)
    print("📋 登录测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有登录测试通过！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
