"""
认证模块路由
"""
from flask import request
from . import auth_bp
from app.utils import success_response, bad_request, unauthorized
from app.services.auth_service import AuthService
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    Request Body:
        {
            "username": "admin",
            "password": "123456"
        }
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "token": "..."
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return bad_request("请求数据不能为空")
        
        username = data.get('username')
        password = data.get('password')
        
        # 参数验证
        if not username or not password:
            return bad_request("用户名和密码不能为空")
        
        # 调用服务层
        success, result = AuthService.login(username, password)
        
        if success:
            return success_response(data={"token": result}, msg="登录成功")
        else:
            return unauthorized(result)
    
    except Exception as e:
        return bad_request(f"登录失败: {str(e)}")