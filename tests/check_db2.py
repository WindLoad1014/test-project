"""检查数据库中的 suggestions 格式"""
import sys
sys.path.append('backend')

from database.db_manager import DatabaseManager

db = DatabaseManager()

# 获取有内容的分析记录
results = db.fetch_all("SELECT email_id, suggestions FROM email_analysis WHERE suggestions != '[]' ORDER BY id DESC LIMIT 10")

print("="*60)
print("📊 数据库中有内容的 suggestions 格式检查")
print("="*60)

if not results:
    print("没有找到包含建议的记录")
    # 获取所有记录看看
    all_results = db.fetch_all("SELECT email_id, suggestions FROM email_analysis ORDER BY id DESC LIMIT 3")
    for row in all_results:
        print(f"\n邮件ID: {row['email_id']}")
        print(f"内容: {row['suggestions']}")
else:
    for row in results:
        email_id = row['email_id']
        suggestions = row['suggestions']
        print(f"\n邮件ID: {email_id}")
        print(f"类型: {type(suggestions)}")
        print(f"内容: {suggestions}")
        print(f"是否是字符串: {isinstance(suggestions, str)}")
        
        if isinstance(suggestions, str):
            import json
            try:
                parsed = json.loads(suggestions)
                print(f"JSON解析成功: {type(parsed)}")
                print(f"解析后内容: {parsed}")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
