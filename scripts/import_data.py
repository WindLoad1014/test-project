"""
将qa_pairs.csv数据导入到数据库
"""
import sys
import os
import pandas as pd
from datetime import datetime

# 添加backend目录到路径
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from database.db_manager import DatabaseManager


def import_qa_pairs_to_knowledge_base(csv_path: str, db_manager: DatabaseManager):
    """将QA对导入到知识库"""
    print(f"📂 读取数据文件: {csv_path}")
    
    # 读取CSV
    df = pd.read_csv(csv_path)
    print(f"📊 共读取 {len(df)} 条记录")
    
    # 导入计数
    imported = 0
    failed = 0
    
    print("\n🔄 开始导入数据...")
    
    for idx, row in df.iterrows():
        try:
            # 构建知识库记录
            record = {
                'question': str(row.get('question_raw', '')).strip(),
                'answer': str(row.get('answer', '')).strip(),
                'question_type': str(row.get('question_type_cn', '其他')).strip(),
                'platform': str(row.get('platform', '未知')).strip(),
                'keywords': '',  # 可以后续提取关键词
                'usage_count': 0,
                'created_at': datetime.now().isoformat()
            }
            
            # 跳过空记录
            if not record['question'] or not record['answer']:
                continue
            
            # 插入数据库
            db_manager.insert('knowledge_base', record)
            imported += 1
            
            # 每100条显示进度
            if (idx + 1) % 100 == 0:
                print(f"  已导入 {idx + 1}/{len(df)} 条...")
                
        except Exception as e:
            failed += 1
            if failed <= 5:  # 只显示前5个错误
                print(f"  ⚠️ 第 {idx + 1} 条导入失败: {e}")
    
    print(f"\n✅ 导入完成!")
    print(f"   成功: {imported} 条")
    print(f"   失败: {failed} 条")
    
    return imported, failed


def import_emails_from_qa_pairs(csv_path: str, db_manager: DatabaseManager):
    """将QA对作为历史邮件导入到emails表"""
    print(f"\n📂 导入历史邮件数据...")
    
    # 读取CSV
    df = pd.read_csv(csv_path)
    
    imported = 0
    
    for idx, row in df.iterrows():
        try:
            # 构建邮件记录
            record = {
                'sender': 'historical@data.com',
                'subject': str(row.get('question_type_cn', '历史数据')),
                'content': str(row.get('question_full', '')).strip(),
                'received_at': str(row.get('problem_time', datetime.now().isoformat())),
                'platform': str(row.get('platform', '')),
                'app_version': str(row.get('app_version', '')),
                'device': str(row.get('device', '')),
                'account_id': '',
                'player_name': '',
                'status': 'replied'  # 历史数据标记为已回复
            }
            
            # 插入邮件
            email_id = db_manager.insert('emails', record)
            
            # 插入分析结果
            analysis = {
                'email_id': email_id,
                'question_type': str(row.get('question_type_cn', '其他')),
                'question_type_confidence': 1.0,
                'urgency': 'low',
                'urgency_confidence': 1.0,
                'urgency_reason': '历史数据',
                'sentiment': 'neutral',
                'sentiment_confidence': 1.0,
                'suggestions': '[]',
                'similar_cases': '[]'
            }
            db_manager.insert('email_analysis', analysis)
            
            # 插入回复
            reply = {
                'email_id': email_id,
                'content': str(row.get('answer', '')).strip(),
                'generated_by': 'historical_data',
                'confidence': 1.0,
                'is_auto_generated': False,
                'is_sent': True,
                'sent_at': record['received_at']
            }
            db_manager.insert('replies', reply)
            
            imported += 1
            
            if (idx + 1) % 100 == 0:
                print(f"  已导入 {idx + 1}/{len(df)} 条...")
                
        except Exception as e:
            if idx < 5:
                print(f"  ⚠️ 第 {idx + 1} 条导入失败: {e}")
    
    print(f"✅ 历史邮件导入完成: {imported} 条")
    
    return imported


def main():
    """主函数"""
    print("="*80)
    print("📥 数据导入工具")
    print("="*80)
    
    # 初始化数据库
    db = DatabaseManager()
    db.init_database()
    
    # CSV文件路径
    csv_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'processed_data', 
        'qa_pairs.csv'
    )
    
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return
    
    # 导入到知识库
    print("\n" + "="*80)
    print("📚 导入到知识库")
    print("="*80)
    imported_kb, failed_kb = import_qa_pairs_to_knowledge_base(csv_path, db)
    
    # 导入历史邮件
    print("\n" + "="*80)
    print("📧 导入历史邮件")
    print("="*80)
    imported_emails = import_emails_from_qa_pairs(csv_path, db)
    
    # 显示统计
    print("\n" + "="*80)
    print("📊 导入统计")
    print("="*80)
    stats = db.get_statistics()
    print(f"知识库条目: {stats.get('total_qa_pairs', 0)}")
    print(f"邮件总数: {stats.get('total_emails', 0)}")
    print(f"已回复: {stats.get('replied_emails', 0)}")
    
    print("\n✅ 数据导入完成!")


if __name__ == '__main__':
    main()
