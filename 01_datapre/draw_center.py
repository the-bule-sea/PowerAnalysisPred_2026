import json
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates
import matplotlib
matplotlib.use('TkAgg')

# 1. 读取 Spark 生成的原始 JSON
with open("center_data.json", "r") as f:
    data = json.load(f)

raw_dates = data['dates']
raw_centers = data['centers']
counts = data['counts']

# 2. 核心修复：将字符串转换为日期对象，并获取正确的排序索引
# 把 "2017/5/1" 转成 datetime 对象
date_objs = [datetime.strptime(d, "%Y/%m/%d") for d in raw_dates]

# 获取能够让日期从小到大排序的“索引数组” (argsort)
sorted_indices = np.argsort(date_objs)

# 3. 同步重排 X 轴 (日期) 和 Y 轴 (聚类中心数据)
sorted_dates = [date_objs[i] for i in sorted_indices]

sorted_centers = []
for center in raw_centers:
    # 将原本乱序的中心数组，按照正确的日期索引重新排列
    sorted_center = np.array(center)[sorted_indices].tolist()
    sorted_centers.append(sorted_center)

# 4. 绘制高颜值的论文配图
plt.figure(figsize=(15, 6))
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示为方块的问题

# 使用更好看的配色
colors = ['#FF6B6B', '#4ECDC4', '#8045D1']

for i in range(3):
    plt.plot(sorted_dates, sorted_centers[i], color=colors[i],
             label=f'Class {i} (Count: {counts[i]})', linewidth=2, alpha=0.85)

plt.title('用户群体用电行为模式聚类分析 (K=3)', fontsize=16)
plt.xlabel('日期', fontsize=12)
plt.ylabel('归一化日总用电量 (0-1)', fontsize=12)

# 优化 X 轴显示格式（按月份显示，避免日期全部挤在一起）
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1)) # 每1个月显示一次刻度
plt.gcf().autofmt_xdate() # 自动旋转 X 轴标签，防止重叠

plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()

# 显示并保存图片
plt.savefig('kmeans_centers_corrected.png', dpi=300)
plt.show()

# 5. (可选) 导出清洗排序后的一份标准 JSON，为后续开发做准备
clean_output = {
    "dates": [d.strftime("%Y/%m/%d") for d in sorted_dates],
    "centers": sorted_centers,
    "counts": counts
}
with open("center_data_sorted.json", "w") as f:
    json.dump(clean_output, f)