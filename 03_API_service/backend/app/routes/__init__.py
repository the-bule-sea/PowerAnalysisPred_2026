"""API路由层包"""
from flask import Blueprint
# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
cluster_bp = Blueprint('cluster', __name__, url_prefix='/api/cluster')
industry_bp = Blueprint('industry', __name__, url_prefix='/api/industry')
map_bp = Blueprint('map', __name__, url_prefix='/api/map')
# 导入路由（避免循环导入）
from . import auth, cluster, industry, map
__all__ = ['auth_bp', 'cluster_bp', 'industry_bp', 'map_bp']