"""测试分析功能"""
import sys
sys.path.append('backend')

from services.ai_service import AIService
from database.db_manager import DatabaseManager
from services.email_service import EmailService

db = DatabaseManager()
ai_service = AIService(db)
email_service = EmailService(db)

# 测试邮件
test_email = {
    'sender': 'test@example.com',
    'subject': '充值未到账',
    'content': '''
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
    ''',
    'platform': 'App Store',
    'app_version': '1.2.0',
    'device': 'iPhone14',
    'account_id': 'TEST123',
    'player_name': 'TestPlayer'
}

print("="*60)
print("🔍 测试邮件分析")
print("="*60)

# 保存邮件
email_id = email_service.save_email(test_email)
print(f"\n邮件已保存，ID: {email_id}")

# 分析邮件
print("\n开始分析...")
analysis_result = ai_service.analyze_email(test_email)

print("\n分析结果:")
print(f"问题类型: {analysis_result['question_type']}")
print(f"紧急度: {analysis_result['urgency']}")
print(f"情感: {analysis_result['sentiment']}")
print(f"\n处理建议:")
for i, suggestion in enumerate(analysis_result['suggestions'], 1):
    print(f"  {i}. {suggestion}")
print(f"\n建议类型: {type(analysis_result['suggestions'])}")

# 保存分析结果
print("\n保存分析结果...")
email_service.save_analysis(email_id, analysis_result)

# 从数据库读取
print("\n从数据库读取...")
loaded_analysis = email_service.get_analysis(email_id)
print(f"\n读取后的建议:")
print(f"类型: {type(loaded_analysis['suggestions'])}")
print(f"内容: {loaded_analysis['suggestions']}")
for i, suggestion in enumerate(loaded_analysis['suggestions'], 1):
    print(f"  {i}. {suggestion}")
