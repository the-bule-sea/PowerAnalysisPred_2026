"""
行业预测模块路由
"""
from flask import request
from . import industry_bp
from app.utils import success_response, bad_request, server_error
from app.services.predict_service import PredictService
@industry_bp.route('/list', methods=['GET'])
def get_industry_list():
    """
    获取行业列表
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": [
                {"id": "1001", "name": "住宿和餐饮业"},
                ...
            ]
        }
    """
    try:
        data = PredictService.get_industry_list()
        return success_response(data=data)
    except Exception as e:
        return server_error(f"获取行业列表失败: {str(e)}")
@industry_bp.route('/predict', methods=['POST'])
def predict_industry():
    """
    执行用电预测
    
    Request Body:
        {
            "industry_id": "1001",
            "model_type": "lstm",
            "future_days": 30
        }
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "dates": [...],
                "values": [...],
                "trend_desc": "..."
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return bad_request("请求数据不能为空")
        
        industry_id = data.get('industry_id')
        model_type = data.get('model_type', 'lstm')
        future_days = data.get('future_days', 30)
        
        # 参数验证
        if not industry_id:
            return bad_request("行业ID不能为空")
        
        if model_type not in ['lstm', 'rf']:
            return bad_request("模型类型必须是 lstm 或 rf")
        
        # 调用服务层
        result = PredictService.predict_industry(industry_id, model_type, future_days)
        
        return success_response(data=result)
    
    except Exception as e:
        return server_error(f"预测失败: {str(e)}")