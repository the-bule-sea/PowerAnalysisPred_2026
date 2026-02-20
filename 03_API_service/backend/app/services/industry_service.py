"""
行业数据服务层
处理行业用电数据的 CSV 导入、分类统计、时序查询等业务逻辑
"""
import pandas as pd
from datetime import datetime
from sqlalchemy import func
from app.models import db
from app.models.industry import IndustryDaily


class IndustryService:
    """行业数据服务类"""
    
    @staticmethod
    def get_industry_categories():
        """
        获取行业分类及其用户数量 (5.3)
        
        Returns:
            dict: 包含一级行业和二级行业的分类信息
            {
                "level1": [
                    {"name": "住宿业", "count": 120},
                    ...
                ],
                "level2": [
                    {"name": "旅游饭店", "parent": "住宿业", "count": 80},
                    ...
                ]
            }
        """
        # 一级行业：按 level1 分组，统计不同 yc_id 数量
        level1_query = db.session.query(
            IndustryDaily.level1,
            func.count(func.distinct(IndustryDaily.yc_id)).label('count')
        ).group_by(IndustryDaily.level1).all()
        
        level1_list = [
            {"name": row.level1, "count": row.count}
            for row in level1_query
        ]
        
        # 二级行业：按 trade_code 分组，同时包含父级行业
        level2_query = db.session.query(
            IndustryDaily.trade_code,
            IndustryDaily.level1,
            func.count(func.distinct(IndustryDaily.yc_id)).label('count')
        ).group_by(IndustryDaily.trade_code, IndustryDaily.level1).all()
        
        level2_list = [
            {"name": row.trade_code, "parent": row.level1, "count": row.count}
            for row in level2_query if row.trade_code
        ]
        
        return {
            "level1": level1_list,
            "level2": level2_list
        }
    
    @staticmethod
    def get_industry_timeseries(level, name, start_date=None, end_date=None):
        """
        获取某行业的每日用电量时间序列 (用于绘制面积图/折线图)
        
        Args:
            level: 层级 (1=一级行业, 2=二级行业)
            name: 行业名称
            start_date: 起始日期 (可选, YYYY-MM-DD)
            end_date: 结束日期 (可选, YYYY-MM-DD)
        
        Returns:
            dict: {"dates": [...], "values": [...]}
        """
        # 根据层级选择分组字段
        if level == 1:
            filter_col = IndustryDaily.level1
        else:
            filter_col = IndustryDaily.trade_code
        
        query = db.session.query(
            IndustryDaily.data_date,
            func.sum(IndustryDaily.daily_usage).label('total_usage')
        ).filter(filter_col == name)
        
        # 日期范围过滤
        if start_date:
            query = query.filter(IndustryDaily.data_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(IndustryDaily.data_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        results = query.group_by(IndustryDaily.data_date) \
                       .order_by(IndustryDaily.data_date) \
                       .all()
        
        dates = [row.data_date.isoformat() for row in results]
        values = [round(row.total_usage, 2) if row.total_usage else 0 for row in results]
        
        return {
            "dates": dates,
            "values": values,
            "name": name,
            "level": level
        }
    
    @staticmethod
    def get_multi_industry_timeseries(level, names, start_date=None, end_date=None):
        """
        获取多个行业的时间序列 (用于堆叠面积图)
        
        Args:
            level: 层级 (1 或 2)
            names: 行业名称列表
            start_date: 起始日期
            end_date: 结束日期
        
        Returns:
            dict: {"dates": [...], "series": [{"name": "xx", "values": [...]}, ...]}
        """
        all_dates = set()
        series_data = {}
        
        for name in names:
            result = IndustryService.get_industry_timeseries(level, name, start_date, end_date)
            all_dates.update(result['dates'])
            series_data[name] = dict(zip(result['dates'], result['values']))
        
        # 排序日期
        sorted_dates = sorted(all_dates)
        
        # 构造对齐的 series
        series = []
        for name in names:
            values = [series_data.get(name, {}).get(d, 0) for d in sorted_dates]
            series.append({"name": name, "values": values})
        
        return {
            "dates": sorted_dates,
            "series": series
        }
    
    @staticmethod
    def import_wide_csv(file_path):
        """
        导入 宽表CSV（每日用电量）到数据库 (5.4)
        
        宽表格式:
        elec_type_code, level1, trade_code, cons_sort_code, yc_id, cons_id, mp_id, start_date, v2020_05_01, v2020_05_02, ...
        
        导入逻辑：
        1. 读取 CSV
        2. 识别维度列和日期列
        3. 将宽表逆透视为长表
        4. 批量写入 IndustryDaily 表
        
        Args:
            file_path: CSV 文件路径
        
        Returns:
            dict: 导入结果统计
        """
        try:
            # 读取 CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 识别日期列 (以 'v20' 开头)
            all_cols = df.columns.tolist()
            date_cols = [c for c in all_cols if c.startswith('v20')]
            dim_cols = [c for c in all_cols if not c.startswith('v20')]
            
            if not date_cols:
                raise ValueError("CSV 中未找到日期列 (v2020_05_01 格式)")
            
            # 逆透视: Wide -> Long
            df_long = df.melt(
                id_vars=dim_cols,
                value_vars=date_cols,
                var_name='raw_date',
                value_name='daily_usage'
            )
            
            # 解析日期: 'v2020_05_01' -> '2020-05-01'
            df_long['data_date'] = pd.to_datetime(
                df_long['raw_date'].str[1:].str.replace('_', '-')
            )
            df_long.drop(columns=['raw_date'], inplace=True)
            
            # 清理数据: NaN -> 0
            df_long['daily_usage'] = df_long['daily_usage'].fillna(0)
            
            # 清空旧数据 (全量覆盖导入)
            IndustryDaily.__table__.drop(db.engine, checkfirst=True)
            IndustryDaily.__table__.create(db.engine, checkfirst=True)
            
            # 批量插入
            total_rows = len(df_long)
            batch_size = 5000
            success_count = 0
            error_count = 0
            errors = []
            
            for i in range(0, total_rows, batch_size):
                batch = df_long.iloc[i:i + batch_size]
                records = []
                
                for _, row in batch.iterrows():
                    try:
                        record = IndustryDaily(
                            elec_type_code=str(row.get('elec_type_code', '')).strip() if pd.notna(row.get('elec_type_code')) else None,
                            level1=str(row.get('level1', '')).strip() if pd.notna(row.get('level1')) else '未知',
                            trade_code=str(row.get('trade_code', '')).strip() if pd.notna(row.get('trade_code')) else None,
                            cons_sort_code=str(row.get('cons_sort_code', '')).strip() if pd.notna(row.get('cons_sort_code')) else None,
                            yc_id=str(row.get('yc_id', '')).strip() if pd.notna(row.get('yc_id')) else '0',
                            cons_id=str(row.get('cons_id', '')).strip() if pd.notna(row.get('cons_id')) else None,
                            mp_id=str(row.get('mp_id', '')).strip() if pd.notna(row.get('mp_id')) else None,
                            data_date=row['data_date'].date(),
                            daily_usage=float(row['daily_usage']) if pd.notna(row['daily_usage']) else 0
                        )
                        records.append(record)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        if len(errors) < 10:
                            errors.append(f"行 {i + _ + 2}: {str(e)}")
                
                db.session.bulk_save_objects(records)
                db.session.commit()
                
                # 打印进度
                progress = min(i + batch_size, total_rows)
                print(f"    导入进度: {progress}/{total_rows} ({progress * 100 // total_rows}%)")
            
            return {
                "success": True,
                "total": total_rows,
                "success_count": success_count,
                "error_count": error_count,
                "date_columns": len(date_cols),
                "errors": errors
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"CSV 导入失败: {str(e)}")
