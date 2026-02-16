"""
用户查询模块路由
"""
import os
from flask import request
from werkzeug.utils import secure_filename
from . import query_bp
from app.utils import success_response, bad_request, server_error
from app.services.query_service import QueryService


@query_bp.route('/users', methods=['GET'])
def get_users():
    """
    获取用户列表（分页）
    
    Query Params:
        page: int (可选) - 页码，默认1
        page_size: int (可选) - 每页数量，默认10
        keyword: str (可选) - 搜索关键词
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "list": [...],
                "total": 1000,
                "page": 1,
                "page_size": 10,
                "total_pages": 100
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', '', type=str)
        
        # 参数验证
        if page < 1:
            return bad_request("页码必须大于0")
        if page_size < 1 or page_size > 100:
            return bad_request("每页数量必须在1-100之间")
        
        # 从数据库查询真实数据
        data = QueryService.get_users_from_db(
            page=page, 
            page_size=page_size,
            keyword=keyword if keyword else None
        )
        
        return success_response(data=data)
    
    except Exception as e:
        return server_error(f"查询用户数据失败: {str(e)}")


@query_bp.route('/upload-csv', methods=['POST'])
def upload_csv():
    """
    上传CSV文件并导入用户数据
    
    Form Data:
        file: CSV文件
    
    Returns:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "success": true,
                "total": 1000,
                "success_count": 980,
                "error_count": 20,
                "errors": [...]
            }
        }
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return bad_request("未选择文件")
        
        file = request.files['file']
        
        if file.filename == '':
            return bad_request("文件名为空")
        
        # 检查文件扩展名
        if not file.filename.endswith('.csv'):
            return bad_request("只支持CSV格式文件")
        
        # 保存文件到临时目录
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        try:
            # 导入数据
            result = QueryService.import_users_from_csv(file_path)
            
            # 删除临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return success_response(data=result, msg="数据导入完成")
        
        except Exception as e:
            # 删除临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    except Exception as e:
        return server_error(f"导入CSV数据失败: {str(e)}")
