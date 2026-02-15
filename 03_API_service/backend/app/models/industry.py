"""
行业数据模型
对应 guide.md 中的表 4-3 行业数据字段
"""
from . import db
class IndustryData(db.Model):
    """行业数据表"""
    
    __tablename__ = 'industry_data'
    
    # 主键：自增序号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增序号')
    
    # 分类信息
    elec_type_code = db.Column(db.String(50), nullable=True, comment='用电类型')
    level1 = db.Column(db.String(100), nullable=True, comment='一级行业')
    trade_code = db.Column(db.String(100), nullable=True, comment='二级行业/所属行业')
    cons_sort_code = db.Column(db.String(50), nullable=True, comment='用户分类')
    
    # 用户信息
    yc_id = db.Column(db.String(50), nullable=True, comment='用采id')
    cons_id = db.Column(db.String(50), nullable=True, comment='用户id')
    
    # 统计数据
    sum = db.Column(db.Float, nullable=True, comment='年总用电量')
    avg = db.Column(db.Float, nullable=True, comment='年平均用电量')
    
    # 创建索引以提升查询性能
    __table_args__ = (
        db.Index('idx_level1', 'level1'),
        db.Index('idx_trade_code', 'trade_code'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'elec_type_code': self.elec_type_code,
            'level1': self.level1,
            'trade_code': self.trade_code,
            'cons_sort_code': self.cons_sort_code,
            'yc_id': self.yc_id,
            'cons_id': self.cons_id,
            'sum': self.sum,
            'avg': self.avg
        }
    
    def __repr__(self):
        return f'<IndustryData {self.level1} - {self.trade_code}>'