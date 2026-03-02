"""
认证服务层
处理用户登录、SHA256+盐密码验证、JWT Token 生成等业务逻辑
"""
import hashlib
import os
from datetime import datetime
from flask_jwt_extended import create_access_token
from app.models import db
from app.models.admin import Admin


class AuthService:
    """认证服务类"""

    # ── 密码工具 ──────────────────────────────────────────
    @staticmethod
    def _generate_salt() -> str:
        """生成 32 字节随机盐（hex 编码，共 64 字符）"""
        return os.urandom(32).hex()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """SHA-256(password + salt) → hex 摘要（64 字符）"""
        raw = (password + salt).encode('utf-8')
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def verify_password(password: str, salt: str, stored_hash: str) -> bool:
        """验证明文密码与数据库存储的哈希是否匹配"""
        return AuthService._hash_password(password, salt) == stored_hash

    # ── 用户管理 ──────────────────────────────────────────
    @staticmethod
    def create_admin(username: str, password: str) -> Admin:
        """
        创建管理员账户（已存在则抛出异常）

        Args:
            username: 用户名
            password: 明文密码

        Returns:
            Admin: 创建的管理员对象
        """
        if Admin.query.filter_by(username=username).first():
            raise ValueError(f"用户名 '{username}' 已存在")

        salt = AuthService._generate_salt()
        password_hash = AuthService._hash_password(password, salt)

        admin = Admin(
            username=username,
            password_hash=password_hash,
            salt=salt,
        )
        db.session.add(admin)
        db.session.commit()
        return admin

    # ── 登录 ──────────────────────────────────────────────
    @staticmethod
    def login(username: str, password: str):
        """
        用户登录验证

        Args:
            username: 用户名
            password: 明文密码

        Returns:
            tuple[bool, str]: (是否成功, JWT token 或错误信息)
        """
        admin = Admin.query.filter_by(username=username).first()

        if not admin:
            return False, "用户名或密码错误"

        if not AuthService.verify_password(password, admin.salt, admin.password_hash):
            return False, "用户名或密码错误"

        # 更新最近登录时间
        admin.last_login = datetime.utcnow()
        db.session.commit()

        # 生成 JWT，identity 携带用户名
        token = create_access_token(identity=admin.username)
        return True, token