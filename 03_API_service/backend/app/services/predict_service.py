"""
行业预测服务层
处理行业用电预测相关业务逻辑
"""
import os
import shutil
import tempfile
import joblib
import numpy as np
from datetime import datetime, timedelta
from flask import current_app
from tensorflow.keras.models import load_model
from app.services.industry_service import IndustryService

class PredictService:
    """预测服务类"""
    
    @staticmethod
    def get_industry_list():
        """
        获取支持预测的行业列表 (对应我们训练过的模型)
        """
        return [
            {"id": "住宿业", "name": "住宿业"},
            {"id": "道路运输业", "name": "道路运输业"}
        ]
    
    @staticmethod
    def predict_industry(industry_id, model_type='lstm', future_days=30):
        """
        执行行业用电预测
        """
        try:
            # 1. 查找历史数据，获取最后 30 天进行预测
            history_data = IndustryService.get_industry_timeseries(level=1, name=industry_id)
            if not history_data or not history_data.get('dates'):
                raise Exception(f"未找到 {industry_id} 的历史数据，请先导入数据！")
            
            dates = history_data['dates']
            values = history_data['values']
            
            if len(values) < 30:
                raise Exception(f"历史数据不足 30 天，无法进行 {model_type} 预测！当前仅有 {len(values)} 天")
                
            last_date_str = dates[-1]
            last_30_values = values[-30:]
            
            # 2. 准备模型路径
            # 当前文件: graduate_code/03_API_service/backend/app/services/predict_service.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.abspath(os.path.join(current_dir, "../../../../01_datapre/models"))
            
            model_path = os.path.join(models_dir, f'{model_type}_model_{industry_id}.h5')
            scaler_path = os.path.join(models_dir, f'scaler_{industry_id}.pkl')
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                 raise Exception(f"未找到 {industry_id} 的预训练模型或 Scaler 文件！请先训练对应行业的模型。")
                 
            # 3. 加载模型与 Scaler
            # Windows 下 HDF5 无法处理中文路径，需要先复制到临时纯 ASCII 路径
            tmp_dir = tempfile.mkdtemp(prefix="predict_")
            tmp_model = os.path.join(tmp_dir, "model.h5")
            tmp_scaler = os.path.join(tmp_dir, "scaler.pkl")
            shutil.copy2(model_path, tmp_model)
            shutil.copy2(scaler_path, tmp_scaler)
            
            try:
                model = load_model(tmp_model)
                scaler = joblib.load(tmp_scaler)
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            
            # 4. 数据预处理
            # 转换为二维并缩放
            input_data = np.array(last_30_values).reshape(-1, 1)
            input_scaled = scaler.transform(input_data)
            
            # 5. 滑动窗口自回归预测
            current_window = input_scaled.reshape((1, 30, 1))
            predictions_scaled = []
            
            for _ in range(future_days):
                # 预测下一天
                next_pred = model.predict(current_window, verbose=0)
                predictions_scaled.append(next_pred[0, 0])
                
                # 滚动窗口：去掉第一天，放入预测出的新一天
                next_pred_reshaped = next_pred.reshape(1, 1, 1)
                current_window = np.append(current_window[:, 1:, :], next_pred_reshaped, axis=1)
                
            # 6. 反归一化
            predictions_scaled_arr = np.array(predictions_scaled).reshape(-1, 1)
            final_predictions = scaler.inverse_transform(predictions_scaled_arr).flatten().tolist()
            
            # 7. 生成未来日期序列
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
            future_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, future_days + 1)]
            
            # 简单趋势描述生成
            growth_rate = (final_predictions[-1] - final_predictions[0]) / final_predictions[0] * 100 if final_predictions[0] != 0 else 0
            trend = "上升" if growth_rate > 0 else "下降"
            
            return {
                "dates": future_dates,
                "values": [round(v, 2) for v in final_predictions],
                "history_dates": dates[-30:],
                "history_values": last_30_values,
                "trend_desc": f"预计未来 {future_days} 天该行业用电量呈{trend}趋势，收尾变动幅率为 {growth_rate:.2f}%。"
            }
        except Exception as e:
            raise Exception(f"预测失败: {str(e)}")
