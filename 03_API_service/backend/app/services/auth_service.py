"""
认证服务层
处理用户登录、JWT Token生成等业务逻辑
"""
from flask_jwt_extended import create_access_token
class AuthService:
    """认证服务类"""
    
    @staticmethod
    def login(username, password):
        """
        用户登录验证
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            tuple: (是否成功, token或错误信息)
        """
        # TODO: 实际项目中应该从数据库验证用户
        # 这里使用硬编码的管理员账户作为示例
        if username == "admin" and password == "123456":
            # 创建JWT token
            token = create_access_token(identity=username)
            return True, token
        else:
            return False, "用户名或密码错误"