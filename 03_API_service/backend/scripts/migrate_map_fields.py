"""
迁移脚本：从 user_cluster.csv 和 user_daily.csv 填充数据库
运行方式（在 backend 目录下执行）：
    python scripts/migrate_map_fields.py

前置条件（在 01_datapre/ 目录运行 get_centers.py 后得到）：
  - 01_datapre/user_cluster.csv  : yc_id, cluster
  - 01_datapre/user_daily.csv    : yc_id, data_date, pap_r, pap_r1, pap_r2

功能说明：
  Step 1 - DDL  : 为 user_data 添加 cluster_type / total_value 列（幂等）
  Step 2 - 导入  : 将 user_daily.csv 批量写入 electricity_data 表（已存在则跳过）
  Step 3 - 回填  : 从 electricity_data 聚合 total_value 到 user_data
  Step 4 - 聚类  : 从 user_cluster.csv 写入 user_data.cluster_type
  Step 5 - 验证  : 打印统计摘要
"""
import sys
import os
import sqlite3
import time
import csv

# ===== 路径配置 =====
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
# 向上跳两级：从 backend -> 03_API_service -> graduate_code(根目录)
PROJECT_DIR = os.path.dirname(os.path.dirname(BACKEND_DIR))

DB_PATH          = os.path.join(BACKEND_DIR, 'instance', 'power_analysis.db')
USER_CLUSTER_CSV = os.path.join(PROJECT_DIR, '01_datapre', 'user_cluster.csv')
USER_DAILY_CSV   = os.path.join(PROJECT_DIR, '01_datapre', 'user_daily.csv')


def get_conn():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] 数据库不存在: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_column_if_not_exists(cursor, table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = [r['name'] for r in cursor.fetchall()]
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"  [+] 已添加列: {table}.{column}")
    else:
        print(f"  [=] 列已存在: {table}.{column}")


# ─────────────────────────────────────────────
def step1_ddl(conn):
    print("\n[Step 1] 检查并添加新列...")
    c = conn.cursor()
    add_column_if_not_exists(c, 'user_data', 'cluster_type', 'INTEGER')
    add_column_if_not_exists(c, 'user_data', 'total_value',  'REAL')
    conn.commit()


# ─────────────────────────────────────────────
def step2_import_daily(conn):
    """将 user_daily.csv 导入 electricity_data 表（按 yc_id+data_date 去重）"""
    print("\n[Step 2] 导入 user_daily.csv -> electricity_data ...")

    if not os.path.exists(USER_DAILY_CSV):
        print(f"  [SKIP] 文件不存在: {USER_DAILY_CSV}")
        print("         请先运行 01_datapre/get_centers.py 生成该文件")
        return

    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM electricity_data")
    existing_count = c.fetchone()[0]
    if existing_count > 0:
        print(f"  [SKIP] electricity_data 已有 {existing_count:,} 条记录，跳过导入")
        print("         如需重新导入，请先清空表: DELETE FROM electricity_data")
        return

    t0 = time.time()
    batch_size = 5000
    batch = []
    total = success = error = 0

    with open(USER_DAILY_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            try:
                yc_id     = str(row.get('yc_id', '')).strip()
                data_date = str(row.get('data_date', '')).strip()
                if not yc_id or not data_date:
                    error += 1
                    continue

                pap_r  = float(row['pap_r'])  if row.get('pap_r')  not in ('', None) else None
                pap_r1 = float(row['pap_r1']) if row.get('pap_r1') not in ('', None) else None
                pap_r2 = float(row['pap_r2']) if row.get('pap_r2') not in ('', None) else None

                batch.append((yc_id, data_date, pap_r, pap_r1, pap_r2))

                if len(batch) >= batch_size:
                    c.executemany(
                        "INSERT OR IGNORE INTO electricity_data (yc_id, data_date, pap_r, pap_r1, pap_r2) "
                        "VALUES (?, ?, ?, ?, ?)",
                        batch
                    )
                    conn.commit()
                    success += len(batch)
                    batch = []
                    print(f"  已写入 {success:,} / {total:,} 行...", end='\r')

            except Exception as e:
                error += 1

    if batch:
        c.executemany(
            "INSERT OR IGNORE INTO electricity_data (yc_id, data_date, pap_r, pap_r1, pap_r2) "
            "VALUES (?, ?, ?, ?, ?)",
            batch
        )
        conn.commit()
        success += len(batch)

    print(f"  导入完成: 成功 {success:,} | 失败 {error:,} | 耗时 {time.time()-t0:.1f}s")


# ─────────────────────────────────────────────
def step3_fill_total_value(conn):
    """从 electricity_data 聚合年总用电量 -> user_data.total_value"""
    print("\n[Step 3] 回填 total_value（年总用电量）...")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM electricity_data WHERE pap_r IS NOT NULL")
    if c.fetchone()[0] == 0:
        print("  [SKIP] electricity_data 无有效 pap_r 数据")
        return

    t0 = time.time()
    c.execute("""
        UPDATE user_data
        SET total_value = (
            SELECT SUM(pap_r)
            FROM electricity_data
            WHERE electricity_data.yc_id = user_data.yc_id
              AND electricity_data.pap_r IS NOT NULL
        )
        WHERE EXISTS (
            SELECT 1 FROM electricity_data
            WHERE electricity_data.yc_id = user_data.yc_id
              AND electricity_data.pap_r IS NOT NULL
        )
    """)
    conn.commit()
    print(f"  已更新 total_value: {c.rowcount:,} 行 ({time.time()-t0:.1f}s)")


# ─────────────────────────────────────────────
def step4_fill_cluster(conn):
    """从 user_cluster.csv 写入 user_data.cluster_type"""
    print("\n[Step 4] 导入聚类标签 user_cluster.csv -> user_data.cluster_type ...")

    if not os.path.exists(USER_CLUSTER_CSV):
        print(f"  [SKIP] 文件不存在: {USER_CLUSTER_CSV}")
        print("         请先运行 01_datapre/get_centers.py 生成该文件")
        return

    c = conn.cursor()
    t0 = time.time()
    updated = skipped = 0

    with open(USER_CLUSTER_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            yc_id   = str(row.get('yc_id', '')).strip()
            cluster = row.get('cluster', '').strip()
            if yc_id and cluster.isdigit():
                batch.append((int(cluster), yc_id))

        c.executemany(
            "UPDATE user_data SET cluster_type = ? WHERE yc_id = ?",
            batch
        )
        conn.commit()
        updated = c.rowcount

    print(f"  已更新 cluster_type: {updated:,} 行 ({time.time()-t0:.1f}s)")

    # 打印各类别分布
    c.execute("SELECT cluster_type, COUNT(*) FROM user_data GROUP BY cluster_type ORDER BY cluster_type")
    print("  聚类分布:")
    labels = {0: '中能耗常规型', 1: '低能耗平稳型', 2: '高能耗波动型'}
    for r in c.fetchall():
        label = labels.get(r[0], f'类别{r[0]}') if r[0] is not None else 'NULL'
        print(f"    cluster_type={r[0]} ({label}): {r[1]:,} 人")


# ─────────────────────────────────────────────
def step5_verify(conn):
    print("\n[Step 5] 验证结果...")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM user_data")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_data WHERE userpoint_x IS NOT NULL")
    with_coord = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_data WHERE cluster_type IS NOT NULL")
    with_cluster = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_data WHERE total_value IS NOT NULL")
    with_value = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM electricity_data")
    elec_rows = c.fetchone()[0]

    print(f"  user_data 总行数      : {total:,}")
    print(f"  有经纬度坐标          : {with_coord:,}")
    print(f"  cluster_type 已填充   : {with_cluster:,}")
    print(f"  total_value  已填充   : {with_value:,}")
    print(f"  electricity_data 行数 : {elec_rows:,}")

    # 预览地图接口所需数据
    c.execute("""
        SELECT yc_id, userpoint_x, userpoint_y, cluster_type, total_value
        FROM user_data
        WHERE userpoint_x IS NOT NULL AND cluster_type IS NOT NULL
        LIMIT 5
    """)
    rows = c.fetchall()
    if rows:
        print("\n  地图数据预览（前5条）:")
        print(f"  {'yc_id':<14} {'lng':>12} {'lat':>12} {'cluster':>8} {'total_kwh':>14}")
        print("  " + "-" * 65)
        for r in rows:
            val_str = f"{r['total_value']:.1f}" if r['total_value'] else "NULL"
            print(f"  {r['yc_id']:<14} {r['userpoint_x']:>12.5f} {r['userpoint_y']:>12.5f} "
                  f"{str(r['cluster_type']):>8} {val_str:>14}")


# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  电力地图字段迁移脚本 v2")
    print(f"  DB : {DB_PATH}")
    print(f"  CSV: {USER_CLUSTER_CSV}")
    print("=" * 60)

    conn = get_conn()
    try:
        step1_ddl(conn)
        step2_import_daily(conn)
        step3_fill_total_value(conn)
        step4_fill_cluster(conn)
        step5_verify(conn)
    finally:
        conn.close()

    print("\n[完成] 迁移成功！现在可以调用 /api/map/points 接口验证数据。\n")


if __name__ == '__main__':
    main()
