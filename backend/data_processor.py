"""
数据预处理模块
处理原始邮件数据，提取问答对
"""
import pandas as pd
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
try:
    from config import Config
    DATA_PATH = Config.DATA_PATH if hasattr(Config, 'DATA_PATH') else None
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
    QUESTION_TYPES = Config.QUESTION_TYPES
except ImportError:
    from backend.config import Config
    DATA_PATH = Config.DATA_PATH if hasattr(Config, 'DATA_PATH') else None
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
    QUESTION_TYPES = Config.QUESTION_TYPES


class DataProcessor:
    """数据处理器：清洗和结构化原始邮件数据"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or DATA_PATH
        self.df = None
        self.qa_pairs = []
        
    def load_data(self) -> pd.DataFrame:
        """加载原始Excel数据"""
        print(f"📂 加载数据: {self.data_path}")
        self.df = pd.read_excel(self.data_path)
        print(f"✅ 加载完成: {len(self.df)} 条记录")
        return self.df
    
    def parse_email_content(self, content: str) -> Dict:
        """解析邮件内容，提取结构化字段"""
        if pd.isna(content) or not content:
            return {}
        
        result = {}
        
        # 提取各个字段
        patterns = {
            'account_id': r'アカウントID\s*[:：]\s*(\S*)',
            'player_name': r'プレイヤー名\s*[:：]\s*(\S*)',
            'app_version': r'アプリバージョン\s*[:：]\s*(\S*)',
            'os_version': r'ご利用のOSバージョン\s*[:：]\s*(\S*)',
            'device': r'ご利用端末名\s*[:：]\s*(\S*)',
            'question_type': r'お問い合わせ内容の種類\s*[:：]\s*([^\n]+)',
            'platform': r'ご利用環境\s*[:：]\s*(\S*)',
            'problem_time': r'問題が発生した日時\s*[:：]\s*([^\n]+)',
            'email': r'メールアドレス\s*[:：]\s*(\S*)',
            'question_content': r'お問い合わせ内容\s*[:：]\s*([\s\S]+?)(?:添付ファイル|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, str(content))
            if match:
                result[key] = match.group(1).strip()
            else:
                result[key] = ''
        
        return result
    
    def extract_qa_pairs(self) -> List[Dict]:
        """提取问答对（枝番1=问题，枝番2=答案）"""
        if self.df is None:
            self.load_data()
        
        print("🔍 提取问答对...")
        
        # 按邮件ID分组
        grouped = self.df.groupby('メールID')
        
        qa_pairs = []
        for mail_id, group in grouped:
            group = group.sort_values('メールID枝番')
            
            # 寻找枝番1（玩家问题）和枝番2（客服回复）的组合
            player_msg = group[group['メールID枝番'] == 1]
            cs_msg = group[group['メールID枝番'] == 2]
            
            if not player_msg.empty and not cs_msg.empty:
                # 解析玩家问题
                player_content = player_msg.iloc[0]['本文']
                player_parsed = self.parse_email_content(player_content)
                
                # 获取客服回复（去除引用部分）
                cs_content = cs_msg.iloc[0]['本文']
                cs_clean = self.clean_cs_response(cs_content)
                
                qa_pair = {
                    'mail_id': int(mail_id),
                    'question_type': player_parsed.get('question_type', ''),
                    'question_type_cn': QUESTION_TYPES.get(player_parsed.get('question_type', ''), '其他'),
                    'platform': player_parsed.get('platform', ''),
                    'device': player_parsed.get('device', ''),
                    'app_version': player_parsed.get('app_version', ''),
                    'problem_time': player_parsed.get('problem_time', ''),
                    'question_raw': player_parsed.get('question_content', ''),
                    'question_full': str(player_content) if not pd.isna(player_content) else '',
                    'answer': cs_clean,
                    'answer_raw': str(cs_content) if not pd.isna(cs_content) else ''
                }
                
                # 只保留有效问答对
                if qa_pair['question_raw'] and qa_pair['answer']:
                    qa_pairs.append(qa_pair)
        
        self.qa_pairs = qa_pairs
        print(f"✅ 提取完成: {len(qa_pairs)} 个有效问答对")
        return qa_pairs
    
    def clean_cs_response(self, content: str) -> str:
        """清洗客服回复，去除引用部分"""
        if pd.isna(content) or not content:
            return ''
        
        content = str(content)
        
        # 去除引用部分（通常以 > 开头）
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            if not line.strip().startswith('>'):
                clean_lines.append(line)
        
        clean_content = '\n'.join(clean_lines).strip()
        
        # 去除多余的空行
        clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
        
        return clean_content
    
    def save_processed_data(self):
        """保存处理后的数据"""
        if not self.qa_pairs:
            self.extract_qa_pairs()
        
        # 保存为JSON
        json_path = PROCESSED_DATA_PATH / "qa_pairs.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=2)
        
        # 保存为CSV（便于查看）
        df = pd.DataFrame(self.qa_pairs)
        csv_path = PROCESSED_DATA_PATH / "qa_pairs.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"💾 数据已保存:")
        print(f"   - JSON: {json_path}")
        print(f"   - CSV: {csv_path}")
        
        return json_path, csv_path
    
    def get_statistics(self) -> Dict:
        """获取数据统计信息"""
        if not self.qa_pairs:
            self.extract_qa_pairs()
        
        df = pd.DataFrame(self.qa_pairs)
        
        stats = {
            'total_qa_pairs': len(self.qa_pairs),
            'question_types': df['question_type_cn'].value_counts().to_dict() if 'question_type_cn' in df.columns else {},
            'platforms': df['platform'].value_counts().to_dict() if 'platform' in df.columns else {},
            'avg_question_length': df['question_raw'].str.len().mean() if 'question_raw' in df.columns else 0,
            'avg_answer_length': df['answer'].str.len().mean() if 'answer' in df.columns else 0
        }
        
        return stats


def main():
    """主函数：处理数据"""
    processor = DataProcessor()
    
    # 加载数据
    processor.load_data()
    
    # 提取问答对
    qa_pairs = processor.extract_qa_pairs()
    
    # 保存处理后的数据
    processor.save_processed_data()
    
    # 打印统计信息
    stats = processor.get_statistics()
    print("\n" + "="*60)
    print("📊 数据统计")
    print("="*60)
    print(f"总问答对数: {stats['total_qa_pairs']}")
    print(f"\n问题类型分布:")
    for qtype, count in stats['question_types'].items():
        print(f"  - {qtype}: {count}")
    print(f"\n平台分布:")
    for platform, count in stats['platforms'].items():
        print(f"  - {platform}: {count}")
    print(f"\n平均问题长度: {stats['avg_question_length']:.0f} 字符")
    print(f"平均回复长度: {stats['avg_answer_length']:.0f} 字符")


if __name__ == "__main__":
    main()
