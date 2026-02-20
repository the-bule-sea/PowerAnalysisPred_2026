# -*- coding: utf-8 -*-
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType

# 1. 初始化
spark = SparkSession.builder \
    .appName("Industry_Power_Clean_V4_SpecificFix") \
    .master("local[*]") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# 2. 读取数据
current_dir = os.path.dirname(os.path.abspath(__file__))
input_csv_name = "raw_data/3.1行业-before_清洗前-utf8.csv" 
input_path = "file://" + os.path.join(current_dir, input_csv_name)

print(f">>> (1/7) 读取数据: {input_path}")
df_raw = spark.read.csv(input_path, header=True, inferSchema=True)
df_raw = df_raw.dropDuplicates()

# 3. 预处理
all_cols = df_raw.columns
date_cols = [c for c in all_cols if c.startswith('v20')]
n_days = len(date_cols)

for c in date_cols:
    df_raw = df_raw.withColumn(c, F.col(c).cast(DoubleType()))

# 4. 逆透视 (保留 cons_id, mp_id)
print(f">>> (2/7) 执行逆透视，共 {n_days} 天...")
stack_expr = f"stack({n_days}, " + \
             ", ".join([f"'{c}', `{c}`" for c in date_cols]) + \
             ") as (raw_date, raw_reading)"

unpivoted_df = df_raw.select("level1", "yc_id", "cons_id", "mp_id", F.expr(stack_expr))

cleaned_df = unpivoted_df.withColumn(
    "data_date",
    F.to_date(F.regexp_replace(F.substring(F.col("raw_date"), 2, 10), "_", "-"))
).drop("raw_date")

# 5. 清洗 0 值
print(">>> (3/7) 清洗累计读数中的 0 值...")
df_null0 = cleaned_df.withColumn("raw_reading", 
                                 F.when(F.col("raw_reading") == 0, None)
                                 .otherwise(F.col("raw_reading")))

# 按表分组填充
w_meter = Window.partitionBy("yc_id", "cons_id", "mp_id").orderBy("data_date")
df_filled = df_null0.withColumn("reading_filled", 
                                F.last("raw_reading", ignorenulls=True).over(w_meter))
df_filled = df_filled.na.fill(0, subset=["reading_filled"])

# 6. 计算日用电量
print(">>> (4/7) 计算日用电量 (Diff)...")
df_usage = df_filled.withColumn("prev_reading", F.lag("reading_filled", 1).over(w_meter)) \
                    .withColumn("daily_usage", F.col("reading_filled") - F.col("prev_reading"))

df_clean_usage = df_usage.withColumn("daily_usage", 
                                     F.when(F.col("daily_usage").isNull(), 0)
                                      .when(F.col("daily_usage") < 0, 0) 
                                      .otherwise(F.col("daily_usage")))

# 7. 聚合
print(">>> (5/7) 按行业聚合...")
final_df = df_clean_usage.groupBy("level1", "data_date") \
    .agg(F.sum("daily_usage").alias("total_power")) \
    .orderBy("level1", "data_date")

# ==============================================================================
#  (V4新增) 精准定点修复逻辑
#  针对 "Day(i)=0, Day(i+1)=Double" 的情况进行平摊
# ==============================================================================
print(">>> (6/7) 执行精准定点修复 (针对全行业缺数导致 0->暴涨 的情况)...")

w_fix = Window.partitionBy("level1").orderBy("data_date")

# 获取前一天是否为0 (is_prev_zero)
# 获取后一天的值 (next_val)
df_calc = final_df.withColumn("is_prev_zero", F.lag(F.col("total_power") == 0, 1).over(w_fix)) \
                  .withColumn("next_val", F.lead("total_power", 1).over(w_fix))

# 执行修复逻辑:
# 1. 补坑: 如果自己是0, 且明天有值 -> 取明天的一半
# 2. 削峰: 如果昨天是0 -> 取自己的一半 (因为自己包含了昨天的量)
# 3. 正常: 保持原样

fixed_df = df_calc.withColumn("total_power_fixed", 
    F.when(F.col("total_power") == 0, F.col("next_val") / 2)  # 情况1: 补坑
     .when(F.col("is_prev_zero") == True, F.col("total_power") / 2) # 情况2: 削峰
     .otherwise(F.col("total_power")) # 情况3: 正常
)

# 再次处理边界情况: 如果最后一天是0且没有next_val, 或者第一天, 保持原样
# 上面的逻辑中 next_val 为 null 时结果会为 null, 需要填充回原值(0)
final_df_v4 = fixed_df.withColumn("total_power", 
                                  F.coalesce(F.col("total_power_fixed"), F.col("total_power"))) \
                      .select("level1", "data_date", "total_power")

print("--- 检查精修后的数据 (房地产业 1.10 - 1.18) ---")
final_df_v4.filter(F.col("level1") == "房地产业") \
           .filter(F.col("data_date").between("2021-01-09", "2021-01-19")) \
           .show(20)

# 8. 保存
output_folder = "cleaned_industry_data_v4_fixed"
output_path = "file://" + os.path.join(current_dir, output_folder)
print(f">>> (7/7) 保存结果到: {output_path}")

final_df_v4.coalesce(1).write.csv(output_path, header=True, mode="overwrite")
spark.stop()
