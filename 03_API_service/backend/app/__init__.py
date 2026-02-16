"""
Flask应用工厂
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import config
from app.models import db
def create_app(config_name='default'):
    """
    创建Flask应用实例
    
    Args:
        config_name: 配置名称 (development/production/default)
    
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    JWTManager(app)
    
    # 注册蓝图
    from app.routes import auth_bp, query_bp, cluster_bp, industry_bp, map_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(cluster_bp)
    app.register_blueprint(industry_bp)
    app.register_blueprint(map_bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 根路由
    @app.route('/')
    def index():
        return {
            "code": 200,
            "msg": "用电行为分析与行业用电预测平台 API Service",
            "version": "1.0.0"
        }
    
    # 健康检查
    @app.route('/health')
    def health():
        return {"status": "healthy", "code": 200}
    
    return app