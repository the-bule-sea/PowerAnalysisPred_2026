"""
行业预测服务层
处理行业用电量预测相关业务逻辑
支持 LSTM 和 Random Forest 两种算法
"""
import os
import shutil
import tempfile
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import current_app
from tensorflow.keras.models import load_model
from app.services.industry_service import IndustryService

# ===== 特征工程常量 (必须与 rf_prepare.py 中保持一致) =====
LAG_DAYS = [1, 2, 3, 7]
ROLLING_WINDOWS = [7]


class PredictService:
    """预测服务类"""
    
    @staticmethod
    def get_industry_list():
        """
        获取支持预测的行业列表 (对应我们训练过的模型)
        """
        return [
            {"id": "住宿业", "name": "住宿业"},
            {"id": "道路运输业", "name": "道路运输业"},
            {"id": "房地产业", "name": "房地产业"}
        ]
    
    @staticmethod
    def predict_industry(industry_id, model_type='lstm', future_days=30):
        """
        执行行业用电预测，根据 model_type 分发到对应算法
        """
        try:
            # 1. 查找历史数据
            history_data = IndustryService.get_industry_timeseries(level=1, name=industry_id)
            if not history_data or not history_data.get('dates'):
                raise Exception(f"未找到 {industry_id} 的历史数据，请先导入数据！")
            
            dates = history_data['dates']
            values = history_data['values']
            
            if len(values) < 30:
                raise Exception(f"历史数据不足 30 天，无法预测！当前仅有 {len(values)} 天")
            
            # 2. 获取模型目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.abspath(os.path.join(current_dir, "../../../../01_datapre/models"))
            
            # 3. 根据模型类型分发
            if model_type == 'rf':
                return PredictService._predict_rf(
                    industry_id, dates, values, future_days, models_dir
                )
            else:
                return PredictService._predict_lstm(
                    industry_id, dates, values, future_days, models_dir
                )
        except Exception as e:
            raise Exception(f"预测失败: {str(e)}")
    
    # ================================================================
    # LSTM 预测分支
    # ================================================================
    @staticmethod
    def _predict_lstm(industry_id, dates, values, future_days, models_dir):
        """LSTM 滑动窗口预测"""
        model_path = os.path.join(models_dir, f'lstm_model_{industry_id}.h5')
        scaler_path = os.path.join(models_dir, f'scaler_{industry_id}.pkl')
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise Exception(f"未找到 {industry_id} 的 LSTM 模型文件！请先运行 lstm_prepare.py 训练。")
        
        # Windows 下 HDF5 无法处理中文路径，先复制到临时纯 ASCII 路径
        tmp_dir = tempfile.mkdtemp(prefix="predict_lstm_")
        tmp_model = os.path.join(tmp_dir, "model.h5")
        tmp_scaler = os.path.join(tmp_dir, "scaler.pkl")
        shutil.copy2(model_path, tmp_model)
        shutil.copy2(scaler_path, tmp_scaler)

        try:
            model = load_model(tmp_model)
            scaler = joblib.load(tmp_scaler)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        
        input_scaled = scaler.transform(np.array(values).reshape(-1, 1))
        
        # 历史区间单步预测 (One-Step)
        hist_pred_dates, hist_predictions = [], []
        if len(input_scaled) > 30:
            windows = np.array([input_scaled[i:i+30] for i in range(len(input_scaled) - 30)])
            preds_scaled = model.predict(windows, verbose=0)
            hist_predictions = scaler.inverse_transform(preds_scaled).flatten().tolist()
            hist_pred_dates = dates[30:]
        
        # 未来多步滚动预测 (Multi-Step)
        current_window = input_scaled[-30:].reshape((1, 30, 1))
        future_preds_scaled = []
        for _ in range(future_days):
            next_pred = model.predict(current_window, verbose=0)
            future_preds_scaled.append(next_pred[0, 0])
            current_window = np.append(current_window[:, 1:, :], next_pred.reshape(1, 1, 1), axis=1)
        
        future_predictions = scaler.inverse_transform(
            np.array(future_preds_scaled).reshape(-1, 1)
        ).flatten().tolist()
        
        last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
        future_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, future_days + 1)]
        
        growth_rate = (future_predictions[-1] - future_predictions[0]) / future_predictions[0] * 100 if future_predictions[0] != 0 else 0
        trend = "上升" if growth_rate > 0 else "下降"
        
        return {
            "actual_dates": dates,
            "actual_values": values,
            "predict_dates": hist_pred_dates + future_dates,
            "predict_values": [round(v, 2) for v in (hist_predictions + future_predictions)],
            "trend_desc": f"[LSTM] 预计未来 {future_days} 天该行业用电量呈{trend}趋势，收尾变动幅率为 {growth_rate:.2f}%。"
        }
    
    # ================================================================
    # Random Forest 预测分支
    # ================================================================
    @staticmethod
    def _build_rf_features(dates, values):
        """
        在线复现特征工程 —— 必须与 rf_prepare.py 中的 create_features() 完全一致
        输入: dates (list[str]), values (list[float])
        输出: DataFrame (含特征列)，以及特征列名列表
        """
        df = pd.DataFrame({
            'data_date': pd.to_datetime(dates),
            'total_power': values
        }).sort_values('data_date').reset_index(drop=True)
        
        # 时间派生特征
        df['day_of_week']   = df['data_date'].dt.dayofweek
        df['is_weekend']    = df['day_of_week'].isin([5, 6]).astype(int)
        df['month']         = df['data_date'].dt.month
        df['day_of_month']  = df['data_date'].dt.day
        
        # 滞后特征
        for lag in LAG_DAYS:
            df[f'lag_{lag}'] = df['total_power'].shift(lag)
        
        # 滚动统计特征
        for window in ROLLING_WINDOWS:
            df[f'rolling_mean_{window}'] = df['total_power'].shift(1).rolling(window=window).mean()
            df[f'rolling_std_{window}']  = df['total_power'].shift(1).rolling(window=window).std()
        
        feature_cols = [c for c in df.columns if c not in ['data_date', 'total_power']]
        return df, feature_cols
    
    @staticmethod
    def _predict_rf(industry_id, dates, values, future_days, models_dir):
        """Random Forest 特征工程 + 预测"""
        model_path    = os.path.join(models_dir, f'rf_model_{industry_id}.pkl')
        scaler_path   = os.path.join(models_dir, f'rf_scaler_{industry_id}.pkl')
        features_path = os.path.join(models_dir, f'rf_features_{industry_id}.pkl')
        
        if not os.path.exists(model_path):
            raise Exception(f"未找到 {industry_id} 的随机森林模型！请先运行 rf_prepare.py 训练。")
        
        rf_model      = joblib.load(model_path)
        scaler        = joblib.load(scaler_path)
        saved_features = joblib.load(features_path)  # 训练时使用的特征列名，用于对齐
        
        # 构建全量历史特征表
        df_all, feature_cols = PredictService._build_rf_features(dates, values)
        df_valid = df_all.dropna().reset_index(drop=True)  # 去掉因滞后产生的 NaN 行
        
        # ---- 历史区间单步预测 ----
        X_hist = df_valid[saved_features].values
        X_hist_scaled = scaler.transform(X_hist)
        hist_predictions = rf_model.predict(X_hist_scaled).tolist()
        hist_pred_dates  = df_valid['data_date'].dt.strftime('%Y-%m-%d').tolist()
        
        # ---- 未来多步逐日预测 ----
        # RF 没有隐状态，必须逐天生成下一天再追加到历史里进行下一轮计算
        future_predictions = []
        future_dates = []
        
        # 维护一个可追加的滑动 DataFrame
        df_rolling = df_all.copy()
        
        last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
        
        for i in range(1, future_days + 1):
            next_date = last_date + timedelta(days=i)
            next_date_str = next_date.strftime('%Y-%m-%d')
            
            # 新增一行（total_power 先用 NaN 占位，特征列后面填充）
            new_row = pd.DataFrame({
                'data_date': [next_date],
                'total_power': [np.nan]
            })
            df_rolling = pd.concat([df_rolling, new_row], ignore_index=True)
            
            # 整体重算特征（包含新追加的这行）
            df_rolling, fc = PredictService._build_rf_features(
                df_rolling['data_date'].dt.strftime('%Y-%m-%d').tolist(),
                df_rolling['total_power'].tolist()
            )
            
            # 取最后一行（即刚追加的这天）进行预测
            last_row = df_rolling.iloc[[-1]][saved_features].values
            last_row_scaled = scaler.transform(last_row)
            next_pred = rf_model.predict(last_row_scaled)[0]
            
            # 把预测值写回到 df_rolling，为下一轮服务（滚动自回归）
            df_rolling.loc[df_rolling.index[-1], 'total_power'] = next_pred
            
            future_predictions.append(round(float(next_pred), 2))
            future_dates.append(next_date_str)
        
        growth_rate = (future_predictions[-1] - future_predictions[0]) / future_predictions[0] * 100 if future_predictions[0] != 0 else 0
        trend = "上升" if growth_rate > 0 else "下降"
        
        return {
            "actual_dates": dates,
            "actual_values": values,
            "predict_dates": hist_pred_dates + future_dates,
            "predict_values": [round(v, 2) for v in hist_predictions] + future_predictions,
            "trend_desc": f"[随机森林] 预计未来 {future_days} 天该行业用电量呈{trend}趋势，收尾变动幅率为 {growth_rate:.2f}%。"
        }

        """
        执行行业用电预测
        """
        try:
            # 1. 查找历史数据，获取全部历史进行预测对比
            history_data = IndustryService.get_industry_timeseries(level=1, name=industry_id)
            if not history_data or not history_data.get('dates'):
                raise Exception(f"未找到 {industry_id} 的历史数据，请先导入数据！")
            
            dates = history_data['dates']
            values = history_data['values']
            
            if len(values) < 30:
                raise Exception(f"历史数据不足 30 天，无法进行 {model_type} 预测！当前仅有 {len(values)} 天")
                
            last_date_str = dates[-1]
            
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
            # 将所有历史数据转换为二维并缩放
            input_data = np.array(values).reshape(-1, 1)
            input_scaled = scaler.transform(input_data)
            
            # 5. 组装历史数据的滑动窗口，用于“历史真实对比”预测 (One-Step Prediction)
            windows = []
            for i in range(len(input_scaled) - 30):
                windows.append(input_scaled[i:i+30])
            windows_np = np.array(windows) # 形状 (N-30, 30, 1)
            
            if len(windows_np) > 0:
                hist_predictions_scaled = model.predict(windows_np, verbose=0)
                hist_predictions = scaler.inverse_transform(hist_predictions_scaled).flatten().tolist()
                hist_pred_dates = dates[30:]
            else:
                hist_predictions = []
                hist_pred_dates = []
            
            # 6. 滑动窗口自回归预测未来 (Multi-Step Prediction)
            current_window = input_scaled[-30:].reshape((1, 30, 1))
            future_predictions_scaled = []
            
            for _ in range(future_days):
                # 预测下一天
                next_pred = model.predict(current_window, verbose=0)
                future_predictions_scaled.append(next_pred[0, 0])
                
                # 滚动窗口：去掉第一天，放入预测出的新一天
                next_pred_reshaped = next_pred.reshape(1, 1, 1)
                current_window = np.append(current_window[:, 1:, :], next_pred_reshaped, axis=1)
                
            # 反归一化未来预测值
            future_predictions_scaled_arr = np.array(future_predictions_scaled).reshape(-1, 1)
            future_predictions = scaler.inverse_transform(future_predictions_scaled_arr).flatten().tolist()
            
            # 7. 生成未来日期序列
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
            future_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, future_days + 1)]
            
            # ==== 组合结果 ====
            all_predict_dates = hist_pred_dates + future_dates
            all_predict_values = [round(v, 2) for v in (hist_predictions + future_predictions)]
            
            # 简单趋势描述生成 (只看未来的增长)
            growth_rate = (future_predictions[-1] - future_predictions[0]) / future_predictions[0] * 100 if future_predictions[0] != 0 else 0
            trend = "上升" if growth_rate > 0 else "下降"
            
            return {
                "actual_dates": dates,
                "actual_values": values,
                "predict_dates": all_predict_dates,
                "predict_values": all_predict_values,
                "trend_desc": f"预计未来 {future_days} 天该行业用电量呈{trend}趋势，收尾变动幅率为 {growth_rate:.2f}%。"
            }
        except Exception as e:
            raise Exception(f"预测失败: {str(e)}")
