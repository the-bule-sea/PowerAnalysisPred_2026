"""
聚类分析服务层
处理用户聚类分析相关业务逻辑
"""
import json
import os
from flask import current_app
class ClusterService:
    """聚类分析服务类"""
    
    @staticmethod
    def get_cluster_centers():
        """
        获取聚类中心曲线数据
        
        Returns:
            dict: 包含日期、中心曲线和用户数量的数据
        """
        try:
            # 读取预处理好的聚类中心数据
            data_path = os.path.join(
                current_app.config['DATA_PRE_PATH'],
                'center_data_sorted.json'
            )
            
            # 实际加载JSON文件
            with open(data_path, 'r', encoding='utf-8') as f:
                center_data = json.load(f)
            
            return center_data
        except Exception as e:
            raise Exception(f"读取聚类中心数据失败: {str(e)}")
    
    @staticmethod
    def get_cluster_stats():
        """
        获取聚类统计分布
        
        Returns:
            list: 各类别的统计信息
        """
        try:
            # 从聚类中心数据中读取counts
            data_path = os.path.join(
                current_app.config['DATA_PRE_PATH'],
                'center_data_sorted.json'
            )
            
            with open(data_path, 'r', encoding='utf-8') as f:
                center_data = json.load(f)
            
            counts = center_data.get('counts', [341, 605, 54])
            
            # 根据图片中的类别标签定义
            return [
                {"name": "Class 0 - 中能耗常规型", "value": counts[0], "label_id": 0},
                {"name": "Class 1 - 低能耗平稳型", "value": counts[1], "label_id": 1},
                {"name": "Class 2 - 高能耗波动型", "value": counts[2], "label_id": 2}
            ]
        except Exception as e:
            raise Exception(f"获取聚类统计数据失败: {str(e)}")