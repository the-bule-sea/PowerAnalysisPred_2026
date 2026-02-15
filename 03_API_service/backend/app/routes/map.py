"""
地图可视化模块路由
"""
from flask import request
from . import map_bp
from app.utils import success_response, server_error
from app.services.map_service import MapService
@map_bp.route('/points', methods=['GET'])
def get_map_points():
    """
    获取用户坐标点集
    
    Query Params:
        limit: int (可选) - 限制返回点数量，默认1000
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": [
                {
                    "yc_id": "10001",
                    "lat": 31.2304,
                    "lng": 121.4737,
                    "type": "高能耗波动型",
                    "value": 4500.5
                },
                ...
            ]
        }
    """
    try:
        # 获取查询参数
        limit = request.args.get('limit', 1000, type=int)
        
        # 调用服务层
        data = MapService.get_user_points(limit=limit)
        
        return success_response(data=data)
    
    except Exception as e:
        return server_error(f"获取地图数据失败: {str(e)}")