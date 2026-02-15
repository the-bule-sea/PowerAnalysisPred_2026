"""
应用配置文件
"""
import os
from datetime import timedelta
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()
class Config:
    """基础配置类"""
    
    # Flask 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///power_analysis.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 生产环境设为False
    
    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # CORS 配置
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    
    # 数据文件路径
    DATA_PRE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '01_datapre')
    TRAINING_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '02_training')
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}