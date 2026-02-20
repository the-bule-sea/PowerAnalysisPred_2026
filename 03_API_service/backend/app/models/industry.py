"""
行业数据模型
包含：
  - IndustryData: 行业汇总表（用户维度信息）
  - IndustryDaily: 行业每日用电明细表（时间序列）
"""
from . import db


class IndustryData(db.Model):
    """行业数据表 (汇总维度)"""
    
    __tablename__ = 'industry_data'
    
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
    
    __table_args__ = (
        db.Index('idx_level1', 'level1'),
        db.Index('idx_trade_code', 'trade_code'),
    )
    
    def to_dict(self):
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


class IndustryDaily(db.Model):
    """行业每日用电明细表 (时间序列)
    
    每一行 = 一个电表(yc_id+cons_id+mp_id) 在某一天(data_date) 的实际用电量(daily_usage)
    由宽表 CSV 导入时自动转为长表存储
    """
    
    __tablename__ = 'industry_daily'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 分类信息
    elec_type_code = db.Column(db.String(50), nullable=True, comment='用电类型')
    level1 = db.Column(db.String(100), nullable=False, comment='一级行业')
    trade_code = db.Column(db.String(100), nullable=True, comment='二级行业')
    cons_sort_code = db.Column(db.String(50), nullable=True, comment='用户分类')
    
    # 用户/电表信息
    yc_id = db.Column(db.String(50), nullable=False, comment='用采id')
    cons_id = db.Column(db.String(50), nullable=True, comment='用户id')
    mp_id = db.Column(db.String(50), nullable=True, comment='计量点id')
    
    # 时间序列核心字段
    data_date = db.Column(db.Date, nullable=False, comment='日期')
    daily_usage = db.Column(db.Float, nullable=True, default=0, comment='当日用电量(Wh)')
    
    __table_args__ = (
        db.Index('idx_daily_level1', 'level1'),
        db.Index('idx_daily_date', 'data_date'),
        db.Index('idx_daily_level1_date', 'level1', 'data_date'),
        db.Index('idx_daily_trade_date', 'trade_code', 'data_date'),
        db.Index('idx_daily_ycid', 'yc_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'level1': self.level1,
            'trade_code': self.trade_code,
            'yc_id': self.yc_id,
            'cons_id': self.cons_id,
            'data_date': self.data_date.isoformat() if self.data_date else None,
            'daily_usage': self.daily_usage
        }
    
    def __repr__(self):
        return f'<IndustryDaily {self.level1} {self.data_date} {self.daily_usage}>'