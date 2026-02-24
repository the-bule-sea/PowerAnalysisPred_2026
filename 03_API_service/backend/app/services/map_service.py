"""
地图可视化服务层
处理地图数据相关业务逻辑
"""
from app.models import db
from app.models.user import UserData


class MapService:
    """地图服务类"""

    # 聚类标签映射
    CLUSTER_LABELS = {
        0: '中能耗常规型',
        1: '低能耗平稳型',
        2: '高能耗波动型',
    }

    @staticmethod
    def get_user_points(limit=1000, cluster_type=None,
                        min_lng=None, max_lng=None,
                        min_lat=None, max_lat=None):
        """
        获取用户坐标点集（直接读 user_data 冗余字段，单表查询）

        Args:
            limit      : 最大返回数量，默认 1000
            cluster_type: 筛选指定聚类类别 (0/1/2)，None 表示全部
            min_lng/max_lng/min_lat/max_lat: 地图视口边界框过滤

        Returns:
            list[dict]: 地图打点数据列表
        """
        try:
            query = UserData.query.filter(
                UserData.userpoint_x.isnot(None),
                UserData.userpoint_y.isnot(None),
            )

            # 聚类类别筛选
            if cluster_type is not None:
                query = query.filter(UserData.cluster_type == cluster_type)

            # 边界框过滤（仅当全部四个参数都提供时生效）
            if all(v is not None for v in [min_lng, max_lng, min_lat, max_lat]):
                query = query.filter(
                    UserData.userpoint_x >= min_lng,
                    UserData.userpoint_x <= max_lng,
                    UserData.userpoint_y >= min_lat,
                    UserData.userpoint_y <= max_lat,
                )

            users = query.limit(limit).all()
            # print("users:",users)

            points = []
            for user in users:
                points.append({
                    'yc_id':        user.yc_id,
                    'lng':          user.userpoint_x,   # 经度
                    'lat':          user.userpoint_y,   # 纬度
                    'cluster_type': user.cluster_type,  # 0/1/2 或 None
                    'type':         MapService.CLUSTER_LABELS.get(
                                        user.cluster_type, '未分类'
                                    ),
                    'value':        round(user.total_value, 2)
                                    if user.total_value is not None else None,
                })

            return points

        except Exception as e:
            raise Exception(f"获取地图数据失败: {str(e)}")