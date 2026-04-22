import os
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    """开发环境：使用 SQLite（无需安装数据库）"""
    DEBUG = True
    # 数据库文件保存在项目目录下的 vote.db
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'vote.db')}"


class MySQLConfig(Config):
    """生产环境：使用 MySQL"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:123456@localhost:3306/vote_db?charset=utf8mb4'
    )


config = {
    'development': DevelopmentConfig,
    'mysql': MySQLConfig,
    'default': DevelopmentConfig   # ← 默认使用 SQLite
}
