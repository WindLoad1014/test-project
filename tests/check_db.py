"""检查数据库中的 suggestions 格式"""
import sys
sys.path.append('backend')

from database.db_manager import DatabaseManager

db = DatabaseManager()

# 获取最新的分析记录
results = db.fetch_all("SELECT email_id, suggestions FROM email_analysis ORDER BY id DESC LIMIT 5")

print("="*60)
print("📊 数据库中的 suggestions 格式检查")
print("="*60)

for row in results:
    email_id = row['email_id']
    suggestions = row['suggestions']
    print(f"\n邮件ID: {email_id}")
    print(f"类型: {type(suggestions)}")
    print(f"内容: {suggestions[:100] if suggestions else 'None'}...")
    print(f"是否是字符串: {isinstance(suggestions, str)}")
    
    if isinstance(suggestions, str):
        import json
        try:
            parsed = json.loads(suggestions)
            print(f"JSON解析成功: {type(parsed)}")
            print(f"解析后内容: {parsed}")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
