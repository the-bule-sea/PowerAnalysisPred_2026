"""
统一响应格式工具
"""
from flask import jsonify
def success_response(data=None, msg="success", code=200):
    """
    成功响应
    
    Args:
        data: 业务数据
        msg: 提示信息
        code: 业务状态码
    
    Returns:
        JSON响应对象
    """
    return jsonify({
        "code": code,
        "msg": msg,
        "data": data if data is not None else {}
    }), 200
def error_response(msg="error", code=500, data=None):
    """
    错误响应
    
    Args:
        msg: 错误信息
        code: 业务状态码
        data: 额外数据
    
    Returns:
        JSON响应对象
    """
    return jsonify({
        "code": code,
        "msg": msg,
        "data": data if data is not None else {}
    }), 200  # HTTP状态码仍为200，业务状态码在code字段
def bad_request(msg="参数错误"):
    """参数错误响应"""
    return error_response(msg=msg, code=400)
def unauthorized(msg="未授权"):
    """未授权响应"""
    return error_response(msg=msg, code=401)
def not_found(msg="资源不存在"):
    """资源不存在响应"""
    return error_response(msg=msg, code=404)
def server_error(msg="服务器内部错误"):
    """服务器错误响应"""
    return error_response(msg=msg, code=500)