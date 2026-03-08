"""
数据库管理器
支持SQLite和MySQL，提供统一的接口
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

try:
    from backend.config import Config
except ImportError:
    from config import Config


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_type: str = None):
        self.db_type = db_type or Config.DATABASE_TYPE
        self.connection = None
        
        if self.db_type == 'sqlite':
            self._init_sqlite()
        elif self.db_type == 'mysql':
            self._init_mysql()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _init_sqlite(self):
        """初始化SQLite数据库"""
        # 确保数据目录存在
        db_dir = os.path.dirname(Config.SQLITE_DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = Config.SQLITE_DB_PATH
        print(f"📂 SQLite数据库: {self.db_path}")
    
    def _init_mysql(self):
        """初始化MySQL数据库连接"""
        try:
            import pymysql
            self.mysql_config = Config.MYSQL_CONFIG
            print(f"🐬 MySQL数据库: {self.mysql_config['host']}:{self.mysql_config['port']}")
        except ImportError:
            print("⚠️ MySQL驱动未安装，请运行: pip install pymysql")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            if self.db_type == 'sqlite':
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
            elif self.db_type == 'mysql':
                import pymysql
                conn = pymysql.connect(**self.mysql_config)
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        print("🔨 初始化数据库...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 邮件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender VARCHAR(255) NOT NULL,
                    subject VARCHAR(500),
                    content TEXT NOT NULL,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    platform VARCHAR(50),
                    app_version VARCHAR(50),
                    device VARCHAR(100),
                    account_id VARCHAR(100),
                    player_name VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 邮件分析表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER NOT NULL,
                    question_type VARCHAR(50),
                    question_type_confidence FLOAT,
                    urgency VARCHAR(20),
                    urgency_confidence FLOAT,
                    urgency_reason TEXT,
                    sentiment VARCHAR(20),
                    sentiment_confidence FLOAT,
                    suggestions TEXT,
                    similar_cases TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails(id)
                )
            ''')
            
            # 回复表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    generated_by VARCHAR(50),
                    confidence FLOAT,
                    is_auto_generated BOOLEAN DEFAULT 0,
                    is_sent BOOLEAN DEFAULT 0,
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails(id)
                )
            ''')
            
            # 知识库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    question_type VARCHAR(50),
                    platform VARCHAR(50),
                    keywords TEXT,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 操作日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation VARCHAR(50) NOT NULL,
                    level VARCHAR(20) DEFAULT 'info',
                    details TEXT,
                    duration_ms FLOAT,
                    user_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'operator',
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ 数据库初始化完成")
            
            # 创建默认管理员账号
            self._create_default_admin()
    
    def _create_default_admin(self):
        """创建默认管理员账号"""
        import hashlib
        
        # 检查是否已有用户
        existing = self.fetch_one("SELECT id FROM users WHERE username = ?", ('admin',))
        if existing:
            return
        
        # 默认密码: admin123
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        
        self.insert('users', {
            'username': 'admin',
            'password_hash': password_hash,
            'email': 'admin@example.com',
            'role': 'admin'
        })
        print("👤 默认管理员账号已创建 (用户名: admin, 密码: admin123)")
    
    def execute(self, sql: str, params: tuple = ()) -> int:
        """执行SQL语句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    
    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        """查询单条记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            
            if row:
                if self.db_type == 'sqlite':
                    return dict(row)
                else:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
            return None
    
    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict]:
        """查询多条记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            if self.db_type == 'sqlite':
                return [dict(row) for row in rows]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入数据"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' if self.db_type == 'sqlite' else '%s'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        return self.execute(sql, tuple(data.values()))
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple) -> int:
        """更新数据"""
        set_clause = ', '.join([f"{k} = ?" if self.db_type == 'sqlite' else f"{k} = %s" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(data.values()) + where_params)
            conn.commit()
            return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: tuple) -> int:
        """删除数据"""
        sql = f"DELETE FROM {table} WHERE {where}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, where_params)
            conn.commit()
            return cursor.rowcount
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        stats = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 邮件统计
            cursor.execute("SELECT COUNT(*) as total FROM emails")
            stats['total_emails'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM emails WHERE status = 'new'")
            stats['new_emails'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM emails WHERE status = 'pending_review'")
            stats['pending_review'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM emails WHERE status = 'replied'")
            stats['replied_emails'] = cursor.fetchone()[0]
            
            # 回复统计
            cursor.execute("SELECT COUNT(*) as total FROM replies")
            stats['total_replies'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM replies WHERE is_auto_generated = 1")
            stats['auto_replies'] = cursor.fetchone()[0]
            
            # 问题类型分布
            cursor.execute('''
                SELECT question_type, COUNT(*) as count 
                FROM email_analysis 
                WHERE question_type IS NOT NULL
                GROUP BY question_type
            ''')
            stats['question_types'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 紧急度分布
            cursor.execute('''
                SELECT urgency, COUNT(*) as count 
                FROM email_analysis 
                WHERE urgency IS NOT NULL
                GROUP BY urgency
            ''')
            stats['urgency_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats


if __name__ == '__main__':
    # 测试数据库管理器
    db = DatabaseManager()
    db.init_database()
    
    # 测试插入
    email_id = db.insert('emails', {
        'sender': 'test@example.com',
        'subject': 'Test Email',
        'content': 'This is a test email'
    })
    print(f"插入邮件ID: {email_id}")
    
    # 测试查询
    result = db.fetch_one("SELECT * FROM emails WHERE id = ?", (email_id,))
    print(f"查询结果: {result}")
    
    # 测试统计
    stats = db.get_statistics()
    print(f"统计信息: {stats}")
