# -*- coding: utf-8 -*-
"""
industry_etl_wide.py
目标：将宽表中每个日期列的【累计读数】替换为【当日用电量（差值）】
输出：宽表格式 CSV，每行=一个电表，每列=当日实际用电量
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType

# ==============================================================================
#  1. 初始化
# ==============================================================================
spark = SparkSession.builder \
    .appName("Industry_ETL_Wide_DailyUsage") \
    .master("local[*]") \
    .config("spark.sql.pivotMaxValues", "1000") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# ==============================================================================
#  2. 读取数据
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
input_csv_name = "raw_data/3.1行业-before_清洗前-utf8.csv"
input_path = "file://" + os.path.join(current_dir, input_csv_name)

print(f">>> (1/6) 读取原始数据: {input_path}")
df_raw = spark.read.csv(input_path, header=True, inferSchema=True)
df_raw = df_raw.dropDuplicates()

# 找出所有维度列（非日期列）和日期列
all_cols = df_raw.columns
date_cols = [c for c in all_cols if c.startswith('v20')]
# 维度列: 除日期列之外的所有列 (elec_type_code, level1, yc_id, cons_id, mp_id ...)
dim_cols = [c for c in all_cols if not c.startswith('v20')]
n_days = len(date_cols)
print(f"    维度列: {dim_cols}")
print(f"    日期列数量: {n_days} 天")

# 强制转换日期列为 Double
for c in date_cols:
    df_raw = df_raw.withColumn(c, F.col(c).cast(DoubleType()))

# ==============================================================================
#  3. 逆透视 (Wide -> Long)
# ==============================================================================
print(f">>> (2/6) 逆透视 (Unpivot)，宽 -> 长...")

stack_expr = f"stack({n_days}, " + \
             ", ".join([f"'{c}', `{c}`" for c in date_cols]) + \
             ") as (raw_date, raw_reading)"

# 选择所有维度列 + stack 表达式
unpivoted_df = df_raw.select(*dim_cols, F.expr(stack_expr))

# 清洗日期格式: 'v2020_05_01' -> '2020-05-01'
unpivoted_df = unpivoted_df.withColumn(
    "data_date",
    F.to_date(F.regexp_replace(F.substring(F.col("raw_date"), 2, 10), "_", "-"))
).drop("raw_date")

# ==============================================================================
#  4. 清洗逻辑 (复用 V4 逻辑：修复大小表问题 + 0值前向填充)
# ==============================================================================
print(">>> (3/6) 清洗 0 值（前向填充）...")
df_null0 = unpivoted_df.withColumn(
    "raw_reading",
    F.when(F.col("raw_reading") == 0, None).otherwise(F.col("raw_reading"))
)

# ★ 关键：按 [yc_id, cons_id, mp_id] 分区，确保同一个电表的数据在同一个分区
# 这里解决了 V2 中"大表小表混算"的问题
w_meter = Window.partitionBy("yc_id", "cons_id", "mp_id").orderBy("data_date")

df_filled = df_null0.withColumn(
    "reading_filled",
    F.last("raw_reading", ignorenulls=True).over(w_meter)
)
df_filled = df_filled.na.fill(0, subset=["reading_filled"])

# ==============================================================================
#  5. 差分计算: 当日用电量 = 今天读数 - 昨天读数
# ==============================================================================
print(">>> (4/6) 差分计算当日用电量...")
df_usage = df_filled \
    .withColumn("prev_reading", F.lag("reading_filled", 1).over(w_meter)) \
    .withColumn("daily_usage", F.col("reading_filled") - F.col("prev_reading"))

# 修正异常：第一天为 null -> 0；换表/读数回退导致负数 -> 0
df_usage = df_usage.withColumn(
    "daily_usage",
    F.when(F.col("daily_usage").isNull(), 0)
     .when(F.col("daily_usage") < 0, 0)
     .otherwise(F.col("daily_usage"))
)

# ==============================================================================
#  6. 逆透视回宽表 (Long -> Wide via Pivot)
#  使用日期列(data_date)作为 pivot 的键，将每天的 daily_usage 还原为列
# ==============================================================================
print(">>> (5/6) 逆透视回宽表 (Pivot)，长 -> 宽...")

# 还原原始日期列名（如 'v2020_05_01'）
df_usage = df_usage.withColumn(
    "col_name",
    F.concat(F.lit("v"), F.date_format(F.col("data_date"), "yyyy_MM_dd"))
)

# 构造 pivot 所需的目标列名列表 (格式还原为 'v2020_05_01')
# date_cols 本身就已经是 'v2020_05_01' 格式了，直接使用即可
target_date_cols = date_cols  # e.g. ['v2020_05_01', 'v2020_05_02', ...]

# 以维度列为 group by，以 col_name 为 pivot，first(daily_usage) 为值
# first 这里只是 pivot 的语法要求，实际上每个 (yc_id+cons_id+mp_id, date) 只有一条记录
df_wide = df_usage.groupBy(*dim_cols).pivot("col_name", target_date_cols).agg(F.first("daily_usage"))

# ==============================================================================
#  7. 保存
# ==============================================================================
output_folder = "industry_wide_daily_usage"
output_path = "file://" + os.path.join(current_dir, output_folder)
print(f">>> (6/6) 保存宽表结果到: {output_path}")
print(f"    列数（维度列 + 日期列）: {len(dim_cols)} + {n_days} = {len(dim_cols) + n_days}")

df_wide.coalesce(1).write.csv(output_path, header=True, mode="overwrite")

print("\n>>> 完成！每个日期列已由【累计读数】替换为【当日用电量】。")
spark.stop()
