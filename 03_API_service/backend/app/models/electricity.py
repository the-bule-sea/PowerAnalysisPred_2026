"""
用户日冻结电量数据模型
对应 guide.md 中的表 4-2 用户日冻结电量数据字段
"""
from . import db
class ElectricityData(db.Model):
    """用户日冻结电量表"""
    
    __tablename__ = 'electricity_data'
    
    # 主键：自增序号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增序号')
    
    # 外键：关联用户表
    yc_id = db.Column(db.String(50), db.ForeignKey('user_data.yc_id'), nullable=False, comment='用采id')
    
    # 统计信息
    sum = db.Column(db.Integer, nullable=True, comment='一年内不为null的电量数据条数')
    cluster = db.Column(db.Integer, nullable=True, comment='聚类类别')
    
    # 电量数据
    pap_r = db.Column(db.Float, nullable=True, comment='用户电量(千瓦时)')
    pap_r1 = db.Column(db.Float, nullable=True, comment='用电峰值')
    pap_r2 = db.Column(db.Float, nullable=True, comment='用电谷值')
    
    # 日期
    data_date = db.Column(db.Date, nullable=False, comment='日期')
    
    # 创建复合索引以提升查询性能
    __table_args__ = (
        db.Index('idx_yc_id_date', 'yc_id', 'data_date'),
        db.Index('idx_cluster', 'cluster'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'yc_id': self.yc_id,
            'sum': self.sum,
            'cluster': self.cluster,
            'pap_r': self.pap_r,
            'pap_r1': self.pap_r1,
            'pap_r2': self.pap_r2,
            'data_date': self.data_date.isoformat() if self.data_date else None
        }
    
    def __repr__(self):
        return f'<ElectricityData {self.yc_id} - {self.data_date}>'