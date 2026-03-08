"""
后端配置文件
支持SQLite和MySQL数据库配置
"""
import os
from pathlib import Path


class Config:
    """基础配置类"""
    
    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent
    
    # 数据文件路径
    PROCESSED_DATA_PATH = BASE_DIR / "processed_data"
    
    # 确保目录存在
    PROCESSED_DATA_PATH.mkdir(exist_ok=True)
    
    # 数据库配置
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')  # 'sqlite' 或 'mysql'
    
    # SQLite配置
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'data/cs_system.db')
    
    # MySQL配置（预留升级接口）
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'cs_system'),
        'charset': 'utf8mb4'
    }
    
    # AI服务配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://coding.dashscope.aliyuncs.com/v1')
    LLM_MODEL = os.getenv('LLM_MODEL', 'qwen3.5-plus')
    
    # 模型配置
    EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
    EMBEDDING_DEVICE = "cpu"
    
    # 向量数据库配置
    VECTOR_DB_PATH = BASE_DIR / "chroma_db"
    COLLECTION_NAME = "customer_service_qa"
    TOP_K = 5
    
    # 邮件服务配置
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    # 系统配置
    AUTO_REPLY_CONFIDENCE_THRESHOLD = float(os.getenv('AUTO_REPLY_THRESHOLD', 0.8))
    MAX_EMAILS_PER_PAGE = int(os.getenv('MAX_EMAILS_PER_PAGE', 50))
    
    # 问题类型映射
    QUESTION_TYPES = {
        "不具合について": "BUG反馈",
        "ご意見?ご要望": "意见建议",
        "アイテム購入時に問題が発生した": "充值问题",
        "アカウントについて": "账号问题",
        "データ復旧について": "数据恢复",
        "その他": "其他"
    }
    
    # 客服回复模板 (日语敬语)
    RESPONSE_TEMPLATES = {
        "BUG反馈": """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

ご迷惑をおかけしておりますことを深くお詫び申し上げます。

{solution}

調査完了後に当窓口よりあらためてご連絡差し上げますので、今しばらくお待ちくださいますようお願いいたします。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。

※本メール内容の無断掲載、無断複製、転送はお控えください。""",

        "意见建议": """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

この度は本ゲームをプレイしていただき、感謝申し上げます。

{solution}

お客様からいただいたお声は貴重なご意見として運営・開発チームに報告し、今後の改善の参考にさせていただきます。

本件以外にもお困りごとやお気づきの点がございましたら、お気軽にお問い合わせください。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。

※本メール内容の無断掲載、無断複製、転送はお控えください。""",

        "充值问题": """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

ご迷惑をおかけしておりますことを深くお詫び申し上げます。

{solution}

至急調査いたしますので、今しばらくお待ちくださいますようお願いいたします。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。

※本メール内容の無断掲載、無断複製、転送はお控えください。""",

        "账号问题": """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

ご連絡いただきありがとうございます。

{solution}

ご不明な点がございましたら、お気軽にお問い合わせください。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。

※本メール内容の無断掲載、無断複製、転送はお控えください。""",

        "数据恢复": """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

ご連絡いただきありがとうございます。

{solution}

データ復旧については、詳細を確認次第ご連絡差し上げます。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。

※本メール内容の無断掲載、無断複製、転送はお控えください。""",

        "其他": """いつもご利用いただきありがとうございます。
『ぽちゃガチョ！』サポート担当です。

ご連絡いただきありがとうございます。

{solution}

ご不明な点がございましたら、お気軽にお問い合わせください。

今後とも『ぽちゃガチョ！』をよろしくお願いいたします。

※本メール内容の無断掲載、無断複製、転送はお控えください。"""
    }
    
    @classmethod
    def get_database_url(cls):
        """获取数据库连接URL"""
        if cls.DATABASE_TYPE == 'sqlite':
            return f"sqlite:///{cls.SQLITE_DB_PATH}"
        elif cls.DATABASE_TYPE == 'mysql':
            config = cls.MYSQL_CONFIG
            return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
        else:
            raise ValueError(f"Unsupported database type: {cls.DATABASE_TYPE}")
    
    @classmethod
    def is_mysql_available(cls):
        """检查MySQL是否可用"""
        try:
            import pymysql
            return True
        except ImportError:
            return False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
