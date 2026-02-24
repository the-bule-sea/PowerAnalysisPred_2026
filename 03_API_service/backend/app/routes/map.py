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
        limit        : int   (可选) 限制返回点数量，默认 1000
        cluster_type : int   (可选) 聚类类别筛选 0/1/2
        min_lng      : float (可选) 边界框最小经度
        max_lng      : float (可选) 边界框最大经度
        min_lat      : float (可选) 边界框最小纬度
        max_lat      : float (可选) 边界框最大纬度

    Returns:
        { "code": 200, "data": [ { yc_id, lng, lat, cluster_type, type, value } ] }
    """
    try:
        limit        = request.args.get('limit', 1000, type=int)
        cluster_type = request.args.get('cluster_type', None, type=int)
        min_lng      = request.args.get('min_lng', None, type=float)
        max_lng      = request.args.get('max_lng', None, type=float)
        min_lat      = request.args.get('min_lat', None, type=float)
        max_lat      = request.args.get('max_lat', None, type=float)

        data = MapService.get_user_points(
            limit=limit,
            cluster_type=cluster_type,
            min_lng=min_lng, max_lng=max_lng,
            min_lat=min_lat, max_lat=max_lat,
        )
        # print("data:",data)
        return success_response(data=data)

    except Exception as e:
        return server_error(f"获取地图数据失败: {str(e)}")