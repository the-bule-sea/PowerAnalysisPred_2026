# -*- coding: utf-8 -*-
"""
fix_117_anomaly.py
目标：针对原始导出的宽表（industry_wide_daily_usage 目录下的 csv），
      使用 Pandas 处理特定日期的异常（1-10 和 1-17 读数为0，导致其后一天用电量暴增）。
方法：将异常那天（如1-11、1-18）的暴增数据取滑动平均（除以2），平摊给缺少数据的前一天（如1-10、1-17）。
"""
import os
import glob
import pandas as pd

def fix_anomaly():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 直接指定文件路径
    input_file = os.path.join(current_dir, "industry_cleaned_daily_v3.csv")
    
    if not os.path.exists(input_file):
        print(f"未找到需要处理的 CSV 文件: {input_file}")
        return
        
    output_file = os.path.join(current_dir, "industry_cleaned_daily_v3_fixed.csv")
    
    print(f">>> (1/4) 读取数据: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 需要处理的异常日期对 (前一天没数据/为0，后一天暴增)
    anomaly_pairs = [
        ('v2021_01_10', 'v2021_01_11'),
        ('v2021_01_17', 'v2021_01_18')
    ]
    
    # 检查列是否存在
    missing_cols = [col for pair in anomaly_pairs for col in pair if col not in df.columns]
    if missing_cols:
        print(f"警告：未找到以下日期列，跳过处理: {missing_cols}")
        anomaly_pairs = [pair for pair in anomaly_pairs if pair[0] in df.columns and pair[1] in df.columns]

    print(f">>> (2/4) 处理异常日期: {anomaly_pairs}")
    
    for day_zero, day_spike in anomaly_pairs:
        # 对原本为 0（或非常小）的 day_zero，且 day_spike 暴增的情况进行平滑
        # 简单策略：如果不加条件，对所有用户这两天都直接做平均计算
        print(f"    正在平滑 {day_zero} 和 {day_spike} ...")
        
        # 计算两天的总和再平分
        smooth_val = (df[day_zero] + df[day_spike]) / 2.0
        
        # 将平均值赋给这两天
        df[day_zero] = smooth_val
        df[day_spike] = smooth_val

    print(f">>> (3/4) 保存修正后的数据到: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(">>> (4/4) 处理完成！一月异常峰值已平滑。")
    print(f"您现在可以使用 {output_file} 来导入前端的数据大屏了！")

if __name__ == "__main__":
    fix_anomaly()
