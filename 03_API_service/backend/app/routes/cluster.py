"""
聚类分析模块路由
"""
from . import cluster_bp
from app.utils import success_response, server_error
from app.services.cluster_service import ClusterService
@cluster_bp.route('/centers', methods=['GET'])
def get_cluster_centers():
    """
    获取聚类中心曲线
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "dates": [...],
                "centers": [...],
                "counts": [...]
            }
        }
    """
    try:
        data = ClusterService.get_cluster_centers()
        return success_response(data=data)
    except Exception as e:
        return server_error(f"获取聚类中心数据失败: {str(e)}")
@cluster_bp.route('/stats', methods=['GET'])
def get_cluster_stats():
    """
    获取聚类统计分布
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": [
                {"name": "...", "value": 341, "label_id": 0},
                ...
            ]
        }
    """
    try:
        data = ClusterService.get_cluster_stats()
        return success_response(data=data)
    except Exception as e:
        return server_error(f"获取聚类统计数据失败: {str(e)}")