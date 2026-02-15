"""
应用入口文件
运行此文件启动Flask服务器
"""
import os
from app import create_app
# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'development'))
if __name__ == '__main__':
    # 运行开发服务器
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )