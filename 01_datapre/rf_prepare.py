import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
import matplotlib.pyplot as plt

# 1. 配置文件路径和参数
INPUT_FILE = 'industry_cleaned_fixed_v5.csv'
TARGET_INDUSTRY = '道路运输业'  # 目标行业
MODEL_DIR = 'models'

# 需要构建的滞后天数
LAG_DAYS = [1, 2, 3, 7]
# 需要构建的滚动窗口大小 (天)
ROLLING_WINDOWS = [7]

def create_features(df):
    """
    为时间序列构建特征工程表
    包括：时间派生特征、滞后特征、滚动统计特征
    """
    df = df.copy()
    df['data_date'] = pd.to_datetime(df['data_date'])
    df = df.sort_values('data_date').reset_index(drop=True)
    
    # --- 1. 时间派生特征 ---
    df['day_of_week'] = df['data_date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['month'] = df['data_date'].dt.month
    df['day_of_month'] = df['data_date'].dt.day
    
    # --- 2. 滞后特征 (Lag Features) ---
    for lag in LAG_DAYS:
        df[f'lag_{lag}'] = df['total_power'].shift(lag)
        
    # --- 3. 滚动统计特征 (Rolling Features) ---
    for window in ROLLING_WINDOWS:
        # shift(1) 保证我们在预测今天时，只能利用截止到昨天为止的历史窗口
        # 例如 rolling_mean_7 就是过去7天（不包含今天）的均值
        df[f'rolling_mean_{window}'] = df['total_power'].shift(1).rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df['total_power'].shift(1).rolling(window=window).std()
        
    # 由于 shift 和 rolling 会导致早期的行出现 NaN，我们需要舍弃这些行
    df.dropna(inplace=True)
    return df

def main():
    print(f">>> 正在读取数据，目标行业: {TARGET_INDUSTRY}")
    df_raw = pd.read_csv(INPUT_FILE)
    df_industry = df_raw[df_raw['level1'] == TARGET_INDUSTRY].copy()
    
    # 填补异常值或初始缺失值
    df_industry['total_power'] = df_industry['total_power'].replace(0, np.nan).interpolate(method='linear').bfill().ffill()
    
    # 特征工程
    print(">>> 正在进行特征工程构造 (Lag/Rolling/Time Features)...")
    df_features = create_features(df_industry)
    
    print(f"--- 构造后的特征表头预览 (前5行) ---")
    print(df_features.head())
    
    # 定义特征列和目标列
    feature_cols = [c for c in df_features.columns if c not in ['level1', 'data_date', 'total_power']]
    target_col = 'total_power'
    
    print("\n>>> 使用的特征列:")
    print(feature_cols)
    
    X = df_features[feature_cols].values
    y = df_features[target_col].values
    dates = df_features['data_date'].values
    
    # 划分训练集和测试集 (80% 训练, 20% 测试)
    # 对于时间序列，不能随机打乱(shuffle=False)，必须按时间截断
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    dates_train, dates_test = dates[:train_size], dates[train_size:]
    
    # 标准化特征 (树模型对量纲不敏感，但标准化有利于模型稳定以及后期加入其他算法横向对比)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 训练随机森林模型
    print("\n>>> 开始训练 Random Forest 评估模型...")
    # n_estimators=100 表示 100 棵树，random_state=42 保证结果可复现
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5, random_state=42)
    rf_model.fit(X_train_scaled, y_train)
    
    # 测试集预测
    print("\n>>> 正在使用测试集进行推断...")
    y_pred = rf_model.predict(X_test_scaled)
    
    # 评估模型
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"评估指标 -> MSE: {mse:.2f}, MAE: {mae:.2f}")
    
    # 保存模型和配套工具
    os.makedirs(MODEL_DIR, exist_ok=True)
    # 保存预测模型
    joblib.dump(rf_model, f'{MODEL_DIR}/rf_model_{TARGET_INDUSTRY}.pkl')
    # 保存缩放器
    joblib.dump(scaler, f'{MODEL_DIR}/rf_scaler_{TARGET_INDUSTRY}.pkl')
    # 额外保存特征列名，方便后端预测时对齐构造字典
    joblib.dump(feature_cols, f'{MODEL_DIR}/rf_features_{TARGET_INDUSTRY}.pkl')
    print(f">>> 模型、Scaler及特征列表已保存至 {MODEL_DIR} 目录！")
    
    # ==========================
    # 可视化结果
    # ==========================
    plt.figure(figsize=(12, 6))
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    plt.plot(y_test, color='red', label='Real Power (真实用电量)', linewidth=2)
    plt.plot(y_pred, color='green', label='RF Predicted (随机森林预测量)', linestyle='--', linewidth=2)
    
    plt.title(f'{TARGET_INDUSTRY} 用电量 随机森林(RF) 预测结果', fontsize=16)
    plt.xlabel('Time (Days in Test Set)', fontsize=12)
    plt.ylabel('Power Consumption (Wh)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(f'rf_prediction_{TARGET_INDUSTRY}.png')
    
    # 特征重要性可视化 (树模型特有的解释性)
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(10, 5))
    plt.title("特征重要性 (Feature Importances)", fontsize=14)
    plt.bar(range(X.shape[1]), importances[indices], align="center")
    plt.xticks(range(X.shape[1]), [feature_cols[i] for i in indices], rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'rf_feature_importances_{TARGET_INDUSTRY}.png')

    print(">>> 可视化结果已保存至当前目录！")
    
    plt.show()

if __name__ == "__main__":
    main()
