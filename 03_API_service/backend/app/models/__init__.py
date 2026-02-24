"""数据库模型包"""
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy()

# 导入所有模型，确保 SQLAlchemy 的 relationship 字符串引用能被正确解析
from .user import UserData
from .electricity import ElectricityData
from .industry import IndustryData

__all__ = ['db', 'UserData', 'ElectricityData', 'IndustryData']
