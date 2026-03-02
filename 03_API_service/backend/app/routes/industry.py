"""
行业模块路由
包含：行业列表、用电预测、行业分类统计、CSV导入、时序数据查询
"""
import os
import tempfile
from flask import request
from flask_jwt_extended import jwt_required
from . import industry_bp
from app.utils import success_response, bad_request, server_error
from app.services.predict_service import PredictService
from app.services.industry_service import IndustryService


@industry_bp.route('/list', methods=['GET'])
@jwt_required()
def get_industry_list():
    """获取行业列表 (5.1)"""
    try:
        data = PredictService.get_industry_list()
        return success_response(data=data)
    except Exception as e:
        return server_error(f"获取行业列表失败: {str(e)}")


@industry_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict_industry():
    """执行用电预测 (5.2)"""
    try:
        data = request.get_json()
        
        if not data:
            return bad_request("请求数据不能为空")
        
        industry_id = data.get('industry_id')
        model_type = data.get('model_type', 'lstm')
        future_days = data.get('future_days', 30)
        
        if not industry_id:
            return bad_request("行业ID不能为空")
        
        if model_type not in ['lstm', 'rf']:
            return bad_request("模型类型必须是 lstm 或 rf")
        
        result = PredictService.predict_industry(industry_id, model_type, future_days)
        return success_response(data=result)
    
    except Exception as e:
        return server_error(f"预测失败: {str(e)}")


@industry_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_industry_categories():
    """
    获取行业分类及其数量 (5.3)
    
    返回一级行业和二级行业的分组统计
    """
    try:
        data = IndustryService.get_industry_categories()
        return success_response(data=data)
    except Exception as e:
        return server_error(f"获取行业分类失败: {str(e)}")


@industry_bp.route('/upload-csv', methods=['POST'])
@jwt_required()
def upload_industry_csv():
    """
    导入行业用电量 CSV (5.4)
    
    接收宽表格式的 CSV 文件（每日用电量），自动转为长表存入数据库
    """
    try:
        if 'file' not in request.files:
            return bad_request("请上传 CSV 文件")
        
        file = request.files['file']
        
        if file.filename == '':
            return bad_request("文件名不能为空")
        
        if not file.filename.endswith('.csv'):
            return bad_request("仅支持 .csv 格式的文件")
        
        # 保存临时文件
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # 调用服务层导入
        result = IndustryService.import_wide_csv(temp_path)
        
        # 清理临时文件
        os.remove(temp_path)
        
        return success_response(data=result, msg="数据导入完成")
    
    except Exception as e:
        return server_error(f"CSV 导入失败: {str(e)}")


@industry_bp.route('/timeseries', methods=['GET'])
@jwt_required()
def get_industry_timeseries():
    """
    获取行业用电量时间序列 (5.5)
    
    Query Parameters:
        level: int (1=一级行业, 2=二级行业)
        name: string (行业名称，多个用逗号分隔)
        start_date: string (起始日期, YYYY-MM-DD, 可选)
        end_date: string (结束日期, YYYY-MM-DD, 可选)
    """
    try:
        level = request.args.get('level', 1, type=int)
        name = request.args.get('name', '')
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if not name:
            return bad_request("行业名称(name)不能为空")
        
        if level not in [1, 2]:
            return bad_request("level 必须是 1 (一级行业) 或 2 (二级行业)")
        
        # 支持多行业查询（逗号分隔）
        names = [n.strip() for n in name.split(',') if n.strip()]
        
        if len(names) == 1:
            data = IndustryService.get_industry_timeseries(level, names[0], start_date, end_date)
        else:
            data = IndustryService.get_multi_industry_timeseries(level, names, start_date, end_date)
        
        return success_response(data=data)
    
    except Exception as e:
        return server_error(f"获取时序数据失败: {str(e)}")


@industry_bp.route('/clear-data', methods=['DELETE'])
@jwt_required()
def clear_industry_data():
    """
    清空所有行业数据 (5.6)
    """
    try:
        IndustryService.delete_all_data()
        return success_response(msg="行业数据已清空")
    except Exception as e:
        return server_error(f"清空数据失败: {str(e)}")
