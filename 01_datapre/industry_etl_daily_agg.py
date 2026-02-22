# -*- coding: utf-8 -*-
"""
industry_etl_daily_agg.py
目标：读取通过 Pandas 修复好异常后的「宽表(日用电量)」(industry_cleaned_daily_v3_fixed.csv)，
      利用 Spark 的算子进行逆透视(Wide -> Long)并按 (一级行业, 日期) 进行聚合汇总，
      最终输出格式为: level1, data_date, total_power 
      直接供 lstm_prepare.py 使用。
"""
import os
import glob
import shutil
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

# 1. 初始化 Spark
spark = SparkSession.builder \
    .appName("Industry_Daily_Agg_LSTM") \
    .master("local[*]") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

current_dir = os.path.dirname(os.path.abspath(__file__))

def main():
    input_file = "industry_cleaned_daily_v3_fixed.csv"
    input_path = "file://" + os.path.join(current_dir, input_file)

    if not os.path.exists(os.path.join(current_dir, input_file)):
        print(f"错误: 未找到输入文件 {input_file} ！请先运行 fix_117_anomaly.py。")
        return

    print(f">>> (1/4) 读取日用电量宽表数据: {input_file}")
    df_raw = spark.read.csv(input_path, header=True, inferSchema=True)

    # 识别以 'v20' 开头的日期列
    all_cols = df_raw.columns
    date_cols = [c for c in all_cols if c.startswith('v20')]
    n_days = len(date_cols)

    # 确保数值格式
    for c in date_cols:
        df_raw = df_raw.withColumn(c, F.col(c).cast(DoubleType()))

    # 2. 逆透视 (Wide -> Long)
    print(f">>> (2/4) 执行逆透视操作，共展开 {n_days} 天...")
    stack_expr = f"stack({n_days}, " + \
                 ", ".join([f"'{c}', `{c}`" for c in date_cols]) + \
                 ") as (raw_date, daily_usage)"

    unpivoted_df = df_raw.select("level1", F.expr(stack_expr))

    # 清洗日期格式: 'v2020_05_01' -> '2020-05-01'
    cleaned_df = unpivoted_df.withColumn(
        "data_date",
        F.to_date(F.regexp_replace(F.substring(F.col("raw_date"), 2, 10), "_", "-"))
    ).drop("raw_date")

    # 兜底处理：确保用电量没有负数或 null (虽然前面清洗过)
    cleaned_df = cleaned_df.withColumn(
        "daily_usage", 
        F.when(F.col("daily_usage").isNull(), 0)
         .when(F.col("daily_usage") < 0, 0)
         .otherwise(F.col("daily_usage"))
    )

    # 3. 按照一级行业聚合汇总
    print(">>> (3/4) 按一级行业与日期聚合总用电量(total_power)...")
    final_df = cleaned_df.groupBy("level1", "data_date") \
        .agg(F.sum("daily_usage").alias("total_power")) \
        .orderBy("level1", "data_date")

    # 查看聚合后的数据样例
    print("\n--- 聚合结果示例 ---")
    final_df.show(5)

    # 4. 保存文件并提取单文件
    output_folder = "industry_cleaned_agg_temp" # 临时输出文件夹
    output_path = "file://" + os.path.join(current_dir, output_folder)
    print(f">>> (4/4) 正在保存聚合结果...")

    final_df.coalesce(1).write.csv(output_path, header=True, mode="overwrite")
    spark.stop()

    # 自动重命名并提取到上一级，变成单文件 industry_cleaned_fixed.csv，无缝对接 lstm_prepare.py
    part_files = glob.glob(os.path.join(current_dir, output_folder, "part-*.csv"))
    if part_files:
        final_csv_target = os.path.join(current_dir, "industry_cleaned_fixed.csv")
        shutil.copy(part_files[0], final_csv_target)
        print(f"\n=======================================================")
        print(f"🎉 成功！已自动将结果提取并保存为: industry_cleaned_fixed.csv")
        print(f"现在您可以直接去运行 lstm_prepare.py 训练了！")
        print(f"=======================================================\n")

if __name__ == "__main__":
    main()
