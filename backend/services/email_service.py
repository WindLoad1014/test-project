"""
邮件服务
处理邮件的接收、存储、查询和发送
"""
import json
from datetime import datetime
from typing import List, Dict, Optional

from backend.database.db_manager import DatabaseManager


class EmailService:
    """邮件服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_email(self, email_data: Dict) -> int:
        """保存邮件到数据库"""
        email_record = {
            'sender': email_data['sender'],
            'subject': email_data.get('subject', ''),
            'content': email_data['content'],
            'received_at': email_data.get('received_at', datetime.now().isoformat()),
            'platform': email_data.get('platform'),
            'app_version': email_data.get('app_version'),
            'device': email_data.get('device'),
            'account_id': email_data.get('account_id'),
            'player_name': email_data.get('player_name'),
            'status': 'new'
        }
        
        return self.db.insert('emails', email_record)
    
    def get_email(self, email_id: int) -> Optional[Dict]:
        """获取邮件基本信息"""
        return self.db.fetch_one(
            "SELECT * FROM emails WHERE id = ?",
            (email_id,)
        )
    
    def get_email_detail(self, email_id: int) -> Optional[Dict]:
        """获取邮件详情（包含分析和回复）"""
        email = self.get_email(email_id)
        if not email:
            return None
        
        # 获取分析结果
        analysis = self.db.fetch_one(
            "SELECT * FROM email_analysis WHERE email_id = ?",
            (email_id,)
        )
        
        # 获取回复
        replies = self.db.fetch_all(
            "SELECT * FROM replies WHERE email_id = ? ORDER BY created_at DESC",
            (email_id,)
        )
        
        email['analysis'] = analysis
        email['replies'] = replies
        
        return email
    
    def get_emails(self, status: str = None, page: int = 1, per_page: int = 20) -> List[Dict]:
        """获取邮件列表"""
        offset = (page - 1) * per_page
        
        if status:
            sql = """
                SELECT e.*, a.question_type, a.urgency 
                FROM emails e
                LEFT JOIN email_analysis a ON e.id = a.email_id
                WHERE e.status = ?
                ORDER BY e.received_at DESC
                LIMIT ? OFFSET ?
            """
            params = (status, per_page, offset)
        else:
            sql = """
                SELECT e.*, a.question_type, a.urgency 
                FROM emails e
                LEFT JOIN email_analysis a ON e.id = a.email_id
                ORDER BY e.received_at DESC
                LIMIT ? OFFSET ?
            """
            params = (per_page, offset)
        
        return self.db.fetch_all(sql, params)
    
    def save_analysis(self, email_id: int, analysis: Dict):
        """保存邮件分析结果"""
        # 检查是否已存在分析
        existing = self.db.fetch_one(
            "SELECT id FROM email_analysis WHERE email_id = ?",
            (email_id,)
        )
        
        analysis_record = {
            'email_id': email_id,
            'question_type': analysis.get('question_type'),
            'question_type_confidence': analysis.get('question_type_confidence'),
            'urgency': analysis.get('urgency'),
            'urgency_confidence': analysis.get('urgency_confidence'),
            'urgency_reason': analysis.get('urgency_reason'),
            'sentiment': analysis.get('sentiment'),
            'sentiment_confidence': analysis.get('sentiment_confidence'),
            'suggestions': json.dumps(analysis.get('suggestions', [])),
            'similar_cases': json.dumps(analysis.get('similar_cases', []))
        }
        
        if existing:
            # 更新
            self.db.update(
                'email_analysis',
                analysis_record,
                'email_id = ?',
                (email_id,)
            )
        else:
            # 插入
            self.db.insert('email_analysis', analysis_record)
    
    def get_analysis(self, email_id: int) -> Optional[Dict]:
        """获取邮件分析结果"""
        analysis = self.db.fetch_one(
            "SELECT * FROM email_analysis WHERE email_id = ?",
            (email_id,)
        )
        
        if analysis:
            # 解析JSON字段
            suggestions = analysis.get('suggestions')
            if suggestions:
                try:
                    if isinstance(suggestions, str):
                        analysis['suggestions'] = json.loads(suggestions)
                    # 如果已经是列表，保持原样
                except json.JSONDecodeError:
                    # JSON解析失败，使用空列表
                    analysis['suggestions'] = []
            else:
                analysis['suggestions'] = []
            
            similar_cases = analysis.get('similar_cases')
            if similar_cases:
                try:
                    if isinstance(similar_cases, str):
                        analysis['similar_cases'] = json.loads(similar_cases)
                except json.JSONDecodeError:
                    analysis['similar_cases'] = []
            else:
                analysis['similar_cases'] = []
        
        return analysis
    
    def save_reply(self, reply_data: Dict) -> int:
        """保存回复"""
        reply_record = {
            'email_id': reply_data['email_id'],
            'content': reply_data['content'],
            'generated_by': reply_data.get('generated_by', 'system'),
            'confidence': reply_data.get('confidence'),
            'is_auto_generated': reply_data.get('is_auto_generated', False),
            'is_sent': False
        }
        
        return self.db.insert('replies', reply_record)
    
    def send_reply(self, email_id: int, content: str) -> Dict:
        """发送回复"""
        # 这里可以实现实际的邮件发送逻辑
        # 目前只是模拟发送，更新数据库状态
        
        sent_at = datetime.now().isoformat()
        
        # 更新回复记录
        self.db.update(
            'replies',
            {'is_sent': True, 'sent_at': sent_at},
            'email_id = ? AND is_sent = 0',
            (email_id,)
        )
        
        # 更新邮件状态
        self.update_status(email_id, 'replied')
        
        return {
            'success': True,
            'sent_at': sent_at,
            'message': 'Reply sent successfully'
        }
    
    def update_status(self, email_id: int, status: str):
        """更新邮件状态"""
        self.db.update(
            'emails',
            {'status': status, 'updated_at': datetime.now().isoformat()},
            'id = ?',
            (email_id,)
        )
    
    def delete_email(self, email_id: int) -> bool:
        """删除邮件及其关联数据"""
        try:
            # 删除相关的回复记录
            self.db.execute(
                "DELETE FROM replies WHERE email_id = ?",
                (email_id,)
            )
            
            # 删除相关的分析记录
            self.db.execute(
                "DELETE FROM email_analysis WHERE email_id = ?",
                (email_id,)
            )
            
            # 删除邮件
            self.db.execute(
                "DELETE FROM emails WHERE id = ?",
                (email_id,)
            )
            
            return True
        except Exception as e:
            print(f"删除邮件失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取邮件统计信息"""
        return self.db.get_statistics()
    
    def parse_email_content(self, content: str) -> Dict:
        """解析邮件内容，提取关键信息"""
        import re
        
        result = {}
        patterns = {
            'account_id': r'アカウントID\s*[:：]\s*(\S*)',
            'player_name': r'プレイヤー名\s*[:：]\s*(\S*)',
            'app_version': r'アプリバージョン\s*[:：]\s*(\S*)',
            'os_version': r'ご利用のOSバージョン\s*[:：]\s*(\S*)',
            'device': r'ご利用端末名\s*[:：]\s*([^\n]+)',
            'question_type': r'お問い合わせ内容の種類\s*[:：]\s*([^\n]+)',
            'platform': r'ご利用環境\s*[:：]\s*(\S*)',
            'question_content': r'お問い合わせ内容\s*[:：]\s*([\s\S]+?)(?:添付ファイル|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, str(content))
            result[key] = match.group(1).strip() if match else ''
        
        return result
