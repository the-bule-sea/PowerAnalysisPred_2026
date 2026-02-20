# -*- coding: utf-8 -*-
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType

# 1. 初始化
spark = SparkSession.builder \
    .appName("Industry_Power_Clean_V3") \
    .master("local[*]") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# 2. 读取数据 (文件名请根据实际情况修改)
current_dir = os.path.dirname(os.path.abspath(__file__))
input_csv_name = "raw_data/3.1行业-before_清洗前-utf8.csv"  # 或者是你实际的文件名
input_path = "file://" + os.path.join(current_dir, input_csv_name)

print(f">>> (1/6) 读取数据: {input_path}")
df_raw = spark.read.csv(input_path, header=True, inferSchema=True)

# 3. 预处理：去重与类型转换
# 防止源数据本身就有完全重复的行
df_raw = df_raw.dropDuplicates()

all_cols = df_raw.columns
date_cols = [c for c in all_cols if c.startswith('v20')]
n_days = len(date_cols)

# 强制转换数值列为 Double
for c in date_cols:
    df_raw = df_raw.withColumn(c, F.col(c).cast(DoubleType()))

# 4. 逆透视 (Unpivot)
print(f">>> (2/6) 执行逆透视，共 {n_days} 天...")
stack_expr = f"stack({n_days}, " + \
             ", ".join([f"'{c}', `{c}`" for c in date_cols]) + \
             ") as (raw_date, raw_reading)"

# ★★★ 关键修改1：保留 cons_id (用户编号) 和 mp_id (计量点编号，如果有的话) ★★★
# 这里假设 cons_id 是区分同一 yc_id 下不同电表的关键
# 如果您的数据里有 mp_id，请务必也加进去： .select("level1", "yc_id", "cons_id", "mp_id", ...
unpivoted_df = df_raw.select("level1", "yc_id", "cons_id", "mp_id", F.expr(stack_expr))

# 清洗日期
cleaned_df = unpivoted_df.withColumn(
    "data_date",
    F.to_date(F.regexp_replace(F.substring(F.col("raw_date"), 2, 10), "_", "-"))
).drop("raw_date")

# ==============================================================================
#  核心修复逻辑 (V3)
# ==============================================================================

# 5. 清洗 0 值
print(">>> (3/6) 清洗累计读数中的 0 值 (Forward Fill)...")
df_null0 = cleaned_df.withColumn("raw_reading",
                                 F.when(F.col("raw_reading") == 0, None)
                                 .otherwise(F.col("raw_reading")))

# ★★★ 关键修改2：按 [yc_id, cons_id] 分组 ★★★
# 这样保证“大表”只跟“大表”比，“小表”只跟“小表”比
w_meter = Window.partitionBy("yc_id", "cons_id", "mp_id").orderBy("data_date")

df_filled = df_null0.withColumn("reading_filled",
                                F.last("raw_reading", ignorenulls=True).over(w_meter))
df_filled = df_filled.na.fill(0, subset=["reading_filled"])

# 6. 计算差值 (日用电量)
print(">>> (4/6) 核心计算：差分计算真实日用电量...")
df_usage = df_filled.withColumn("prev_reading", F.lag("reading_filled", 1).over(w_meter)) \
                    .withColumn("daily_usage", F.col("reading_filled") - F.col("prev_reading"))

# 修正异常：负值归零
df_clean_usage = df_usage.withColumn("daily_usage",
                                     F.when(F.col("daily_usage").isNull(), 0)
                                      .when(F.col("daily_usage") < 0, 0)
                                      .otherwise(F.col("daily_usage")))

# ==============================================================================
#  聚合逻辑
# ==============================================================================

# 7. 聚合
print(">>> (5/6) 按行业聚合...")
final_df = df_clean_usage.groupBy("level1", "data_date") \
    .agg(F.sum("daily_usage").alias("total_power")) \
    .orderBy("level1", "data_date")

print("--- 修正V3版后的数据预览 (重点观察 2020-08-22) ---")
final_df.show(10)

# 检查一下特定日期的值
print("--- 检查 2020-08-22 附近的住宿业数据 ---")
final_df.filter(F.col("level1") == "住宿业") \
        .filter(F.col("data_date").between("2020-08-20", "2020-08-25")) \
        .show()

# 8. 保存
output_folder = "cleaned_industry_data_v3"
output_path = "file://" + os.path.join(current_dir, output_folder)
print(f">>> (6/6) 保存结果到: {output_path}")

final_df.coalesce(1).write.csv(output_path, header=True, mode="overwrite")
spark.stop()
