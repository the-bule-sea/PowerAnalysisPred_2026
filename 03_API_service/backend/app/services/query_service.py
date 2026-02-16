"""
用户查询服务层
处理用户数据查询相关业务逻辑
"""
import pandas as pd
from app.models import db
from app.models.user import UserData


class QueryService:
    """用户查询服务类"""
    
    @staticmethod
    def get_users_from_db(page=1, page_size=10, keyword=None):
        """
        从数据库查询用户数据（分页）
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            keyword: 搜索关键词（可选）
        
        Returns:
            dict: 包含用户列表和分页信息
        """
        query = UserData.query
        
        # 如果有搜索关键词，添加过滤条件
        if keyword:
            query = query.filter(
                db.or_(
                    UserData.yc_id.like(f'%{keyword}%'),
                    UserData.meter_id.like(f'%{keyword}%')
                )
            )
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )
        
        # 转换为字典列表
        users = []
        for idx, user in enumerate(pagination.items, start=(page - 1) * page_size + 1):
            user_dict = user.to_dict()
            user_dict['id'] = idx  # 添加序号
            users.append(user_dict)
        
        return {
            "list": users,
            "total": pagination.total,
            "page": page,
            "page_size": page_size,
            "total_pages": pagination.pages
        }
    
    @staticmethod
    def import_users_from_csv(file_path):
        """
        从CSV文件导入用户数据
        
        Args:
            file_path: CSV文件路径
        
        Returns:
            dict: 导入结果统计
        """
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 字段映射（CSV列名 -> 数据库字段名）
            column_mapping = {
                'yc_id': 'yc_id',
                'meter_id': 'meter_id',
                'build_date': 'build_date',
                'trade_code': 'trade_code',
                'elec_type_code': 'elec_type_code',
                'cons_sort_code': 'cons_sort_code',
                'volt_code': 'volt_code',
                'contract_cap': 'contract_cap',
                'userpoint_x': 'userpoint_x',
                'userpoint_y': 'userpoint_y'
            }
            
            # 重命名列
            df = df.rename(columns=column_mapping)
            
            # 统计信息
            total_rows = len(df)
            success_count = 0
            error_count = 0
            errors = []
            
            # 批量插入
            for idx, row in df.iterrows():
                try:
                    # 检查是否已存在
                    yc_id = str(row.get('yc_id', '')).strip()
                    if not yc_id:
                        error_count += 1
                        errors.append(f"第{idx + 2}行: 用采id为空")
                        continue
                    
                    existing_user = UserData.query.filter_by(yc_id=yc_id).first()
                    
                    if existing_user:
                        # 更新现有记录
                        for key, value in row.items():
                            if key != 'yc_id' and pd.notna(value):
                                # 处理日期字段
                                if key == 'build_date':
                                    try:
                                        value = pd.to_datetime(value).date()
                                    except:
                                        value = None
                                setattr(existing_user, key, value)
                    else:
                        # 创建新记录
                        user_data = {
                            'yc_id': yc_id,
                            'meter_id': str(row.get('meter_id', '')).strip() if pd.notna(row.get('meter_id')) else None,
                            'trade_code': str(row.get('trade_code', '')).strip() if pd.notna(row.get('trade_code')) else None,
                            'elec_type_code': str(row.get('elec_type_code', '')).strip() if pd.notna(row.get('elec_type_code')) else None,
                            'cons_sort_code': str(row.get('cons_sort_code', '')).strip() if pd.notna(row.get('cons_sort_code')) else None,
                            'volt_code': str(row.get('volt_code', '')).strip() if pd.notna(row.get('volt_code')) else None,
                            'contract_cap': float(row.get('contract_cap')) if pd.notna(row.get('contract_cap')) else None,
                            'userpoint_x': float(row.get('userpoint_x')) if pd.notna(row.get('userpoint_x')) else None,
                            'userpoint_y': float(row.get('userpoint_y')) if pd.notna(row.get('userpoint_y')) else None,
                        }
                        
                        # 处理日期
                        if pd.notna(row.get('build_date')):
                            try:
                                user_data['build_date'] = pd.to_datetime(row.get('build_date')).date()
                            except:
                                user_data['build_date'] = None
                        
                        new_user = UserData(**user_data)
                        db.session.add(new_user)
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{idx + 2}行: {str(e)}")
                    continue
            
            # 提交事务
            db.session.commit()
            
            return {
                "success": True,
                "total": total_rows,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10]  # 最多返回前10条错误
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"CSV文件解析失败: {str(e)}")
