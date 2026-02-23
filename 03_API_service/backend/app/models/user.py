"""
用户数据模型
对应 guide.md 中的表 4-1 用户数据字段
"""
from . import db
class UserData(db.Model):
    """用户数据表"""
    
    __tablename__ = 'user_data'
    
    # 主键：用采id
    yc_id = db.Column(db.String(50), primary_key=True, comment='用采id')
    
    # 基础信息
    meter_id = db.Column(db.String(50), nullable=True, comment='表号')
    build_date = db.Column(db.Date, nullable=True, comment='立户日期')
    
    # 分类信息
    trade_code = db.Column(db.String(50), nullable=True, comment='行业分类')
    elec_type_code = db.Column(db.String(50), nullable=True, comment='用电类型')
    cons_sort_code = db.Column(db.String(50), nullable=True, comment='用电分类')
    
    # 电力信息
    volt_code = db.Column(db.String(50), nullable=True, comment='供电电压')
    contract_cap = db.Column(db.Float, nullable=True, comment='合同容量')
    
    # 地理位置
    userpoint_x = db.Column(db.Float, nullable=True, comment='经度')
    userpoint_y = db.Column(db.Float, nullable=True, comment='纬度')

    # 地图冗余快照字段（由迁移脚本从 electricity_data 聚合填充）
    cluster_type = db.Column(db.Integer, nullable=True, comment='聚类类别 (0/1/2)')
    total_value = db.Column(db.Float, nullable=True, comment='年总用电量(千瓦时)')
    
    # 关联关系：一个用户对应多条电量记录
    electricity_records = db.relationship('ElectricityData', backref='user', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'yc_id': self.yc_id,
            'meter_id': self.meter_id,
            'build_date': self.build_date.isoformat() if self.build_date else None,
            'trade_code': self.trade_code,
            'elec_type_code': self.elec_type_code,
            'cons_sort_code': self.cons_sort_code,
            'volt_code': self.volt_code,
            'contract_cap': self.contract_cap,
            'userpoint_x': self.userpoint_x,
            'userpoint_y': self.userpoint_y,
            'cluster_type': self.cluster_type,
            'total_value': self.total_value
        }
    
    def __repr__(self):
        return f'<UserData {self.yc_id}>'