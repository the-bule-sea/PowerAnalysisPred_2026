import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# 1. 配置文件路径和参数
INPUT_FILE = 'industry_cleaned_fixed_v4.csv' # 请替换为你下载的 Spark 结果文件路径
TARGET_INDUSTRY = '住宿业'         # 就拿你截图里的住宿业来练手
TIME_STEP = 30                    # 滑动窗口大小：用过去30天预测第31天

def create_dataset(dataset, time_step=1):
    """
    构造 LSTM 的滑动窗口
    """
    dataX, dataY = [], []
    for i in range(len(dataset) - time_step):
        a = dataset[i:(i + time_step), 0]
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)

# 2. 读取数据 (Pandas 会自动把 E7 解析为正常的小数)
print(f">>> 正在读取数据，目标行业: {TARGET_INDUSTRY}")
df = pd.read_csv(INPUT_FILE)

# 筛选行业
df_industry = df[df['level1'] == TARGET_INDUSTRY].copy()

# 3. 时间序列对齐 (关键)
# pd.to_datetime 会自动搞定 2020/5/1 或 2020-05-01
df_industry['data_date'] = pd.to_datetime(df_industry['data_date'])
df_industry = df_industry.sort_values('data_date').reset_index(drop=True)

# 打印一下看看 E7 是不是被成功转换了
print("\n--- Pandas 解析后的前5条数据 ---")
print(df_industry[['data_date', 'total_power']].head())

# 4. 缺失值与异常值处理
df_industry['total_power'] = df_industry['total_power'].replace(0, np.nan)
df_industry['total_power'] = df_industry['total_power'].interpolate(method='linear')
df_industry['total_power'] = df_industry['total_power'].bfill().ffill()

# 5. 归一化 (Min-Max Scaling)
print("\n>>> 正在进行数据归一化...")
scaler = MinMaxScaler(feature_range=(0, 1))
dataset = df_industry['total_power'].values.reshape(-1, 1)
dataset_scaled = scaler.fit_transform(dataset)

# 保存 Scaler (未来反归一化要用)
os.makedirs('models', exist_ok=True)
joblib.dump(scaler, f'models/scaler_{TARGET_INDUSTRY}.pkl')

# 6. 划分训练集和测试集 (80% 训练, 20% 测试)
train_size = int(len(dataset_scaled) * 0.8)
test_size = len(dataset_scaled) - train_size
train_data = dataset_scaled[0:train_size, :]
test_data = dataset_scaled[train_size:len(dataset_scaled), :]

# 7. 构造三维滑动窗口
X_train, y_train = create_dataset(train_data, TIME_STEP)
X_test, y_test = create_dataset(test_data, TIME_STEP)

# Reshape 为 [样本数, 时间步长, 特征数]
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

print("\n================ 预处理完成 ================")
print(f"训练集特征张量 X_train 形状: {X_train.shape}")
print(f"训练集标签张量 y_train 形状: {y_train.shape}")
print(f"测试集特征张量 X_test 形状: {X_test.shape}")
print(f"测试集标签张量 y_test 形状: {y_test.shape}")
print("============================================")


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt

print("\n>>> 开始构建 LSTM 神经网络模型...")

# ==========================================
# 1. 搭建模型架构 (Model Architecture)
# ==========================================
model = Sequential()

# 第一层 LSTM：神经元个数设为 50
# return_sequences=True 表示输出也是个序列，为了传给下一层 LSTM
# input_shape 就是我们刚才转换的 (30, 1)
model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
model.add(Dropout(0.2)) # 随机丢弃 20% 的神经元，防止模型“死记硬背”(过拟合)

# 第二层 LSTM
model.add(LSTM(units=50, return_sequences=False))
model.add(Dropout(0.2))

# 输出层 (全连接层)：因为只预测明天的 1 个电量值，所以 units=1
model.add(Dense(units=1))

# ==========================================
# 2. 编译模型 (Compilation)
# ==========================================
# 优化器选用最主流的 adam，损失函数选用均方误差(mse)，适合回归预测任务
model.compile(optimizer='adam', loss='mean_squared_error')
print(model.summary()) # 打印模型结构（可以直接截图放进论文）

# ==========================================
# 3. 训练模型 (Training)
# ==========================================
print("\n>>> 开始训练模型...")
# epochs=50 表示把所有数据翻来覆去学 50 遍
# validation_split=0.1 表示从训练集里抽 10% 做验证，边学边考
history = model.fit(X_train, y_train, epochs=50, batch_size=16, validation_split=0.1, verbose=1)

# 保存模型权重 (方便以后 Flask 后端直接调用)
model.save(f'models/lstm_model_{TARGET_INDUSTRY}.h5')
print("\n>>> 模型已保存至 models/ 目录！")

# ==========================================
# 4. 模型评估与预测 (Prediction & Inverse Transform)
# ==========================================
print("\n>>> 正在使用测试集进行预测评估...")
# 让模型预测测试集
predicted_scaled = model.predict(X_test)

# 核心步骤：反归一化！把 0-1 的小数还原成真实的上千万度电
# 注意：y_test 原本是一维的，反归一化需要二维，所以稍微 reshape 一下
real_power = scaler.inverse_transform(y_test.reshape(-1, 1))
predicted_power = scaler.inverse_transform(predicted_scaled)

# ==========================================
# 5. 结果可视化 (Visualization)
# ==========================================
plt.figure(figsize=(12, 6))
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
plt.plot(real_power, color='red', label='Real Power Consumption (真实用电量)', linewidth=2)
plt.plot(predicted_power, color='blue', label='Predicted Power Consumption (预测用电量)', linestyle='--', linewidth=2)
plt.title(f'{TARGET_INDUSTRY} 用电量 LSTM 预测结果', fontsize=16)
plt.xlabel('Time (Days)', fontsize=12)
plt.ylabel('Power Consumption (Wh)', fontsize=12)
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()

# 保存图片用于论文
plt.savefig(f'lstm_prediction_{TARGET_INDUSTRY}.png', dpi=300)
plt.show()

# 在 lstm_prepare.py 末尾加这几行
total_len = len(df_industry)
train_size = int(total_len * 0.8)
print(f"总天数: {total_len}")
print(f"测试集起始日期: {df_industry['data_date'].iloc[train_size]}")
print(f"测试集结束日期: {df_industry['data_date'].iloc[-1]}")