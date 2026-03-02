"""
管理员账户数据模型
"""
from datetime import datetime
from . import db


class Admin(db.Model):
    """管理员账户表"""

    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键')
    username = db.Column(db.String(64), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(64), nullable=False, comment='SHA256密码哈希')
    salt = db.Column(db.String(64), nullable=False, comment='随机盐（hex字符串）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    last_login = db.Column(db.DateTime, nullable=True, comment='最近登录时间')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self):
        return f'<Admin {self.username}>'
