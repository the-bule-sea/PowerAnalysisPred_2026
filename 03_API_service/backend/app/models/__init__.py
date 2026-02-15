"""数据库模型包"""
from flask_sqlalchemy import SQLAlchemy
# 创建数据库实例
db = SQLAlchemy()
# 导入所有模型（在后续创建模型后取消注释）
# from .user import UserData
# from .electricity import ElectricityData
# from .industry import IndustryData
__all__ = ['db']