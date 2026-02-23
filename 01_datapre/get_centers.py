# -*- coding: utf-8 -*-
import os
import json
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, MinMaxScaler
from pyspark.ml.clustering import KMeans

# 1. 初始化
spark = SparkSession.builder.appName("Get_KMeans_Centers").master("local[*]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# 2. 读取数据 (和之前一样)
current_dir = os.path.dirname(os.path.abspath(__file__))
input_path = "file://" + os.path.join(current_dir, "cleaned_power_data_v2")
df = spark.read.csv(input_path, header=True, inferSchema=True)

# 3. 预处理 (和之前完全一样，保证特征一致)
dates_row = df.select("data_date").distinct().sort("data_date").collect()
sorted_dates = [row.data_date for row in dates_row]

pivot_df = df.groupBy("yc_id").pivot("data_date", sorted_dates).sum("pap_r").na.fill(0)
assembler = VectorAssembler(inputCols=sorted_dates, outputCol="features_raw")
vector_df = assembler.transform(pivot_df)
scaler = MinMaxScaler(inputCol="features_raw", outputCol="features")
scaler_model = scaler.fit(vector_df)
final_df = scaler_model.transform(vector_df).select("yc_id", "features")

# 4. 训练 K=3 的最终模型
print(">>> 正在训练 K=3 模型...")
kmeans = KMeans().setK(3).setSeed(1).setFeaturesCol("features")
model = kmeans.fit(final_df)

# 5. 获取聚类中心
# centers 是一个列表，包含3个 array，每个 array 有365个数字
centers = model.clusterCenters()

# 6. 统计每一类的用户数量 (看看哪一类人最多)
predictions = model.transform(final_df)
count_df = predictions.groupBy("prediction").count().orderBy("prediction")
print("\n>>> 各类用户数量统计:")
count_df.show()

# 7. 将中心点数据保存为 JSON，方便你复制去画图
print(">>> 正在导出聚类中心数据...")
centers_list = [c.tolist() for c in centers]
output_data = {
    "dates": sorted_dates,
    "centers": centers_list,
    "counts": [row['count'] for row in count_df.collect()]
}

# 保存到本地文件 center_data.json
with open("center_data.json", "w") as f:
    json.dump(output_data, f)
print(">>> center_data.json 已保存")

# 8. 导出用户聚类标签映射 user_cluster.csv
# 格式: yc_id, cluster
# 用途: 导入数据库后填充 user_data.cluster_type
print(">>> 正在导出用户聚类标签 user_cluster.csv ...")
user_cluster_df = predictions.select("yc_id", "prediction").withColumnRenamed("prediction", "cluster")
user_cluster_pd = user_cluster_df.toPandas()
user_cluster_pd.to_csv("user_cluster.csv", index=False, encoding="utf-8")
print(f">>> user_cluster.csv 已保存，共 {len(user_cluster_pd)} 条记录")
print(user_cluster_pd["cluster"].value_counts().sort_index().to_string())

# 9. 导出原始日电量数据 user_daily.csv
# 格式: yc_id, data_date, pap_r, pap_r1, pap_r2
# 用途: 导入数据库 electricity_data 表
print(">>> 正在导出原始日电量数据 user_daily.csv ...")
daily_cols = ["yc_id", "data_date", "pap_r", "pap_r1", "pap_r2"]
# 只选取存在的列（pap_r1/pap_r2 若不存在则跳过）
available_cols = [c for c in daily_cols if c in df.columns]
user_daily_pd = df.select(available_cols).toPandas()
user_daily_pd.to_csv("user_daily.csv", index=False, encoding="utf-8")
print(f">>> user_daily.csv 已保存，共 {len(user_daily_pd)} 条记录，列: {available_cols}")

spark.stop()
print(">>> 全部输出完成："
      "\n  - center_data.json  (聚类中心曲线)"
      "\n  - user_cluster.csv  (yc_id -> cluster 映射，导入 user_data.cluster_type)"
      "\n  - user_daily.csv    (每日电量明细，导入 electricity_data 表)")