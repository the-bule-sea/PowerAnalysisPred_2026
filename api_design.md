# 电力数据分析与预测平台后端 API 接口文档 (v1.0)

**—— Python Flask 架构**

## 1. 系统架构与环境约定

本系统后端采用 **轻量级服务架构**，业务服务层：

* **业务服务层 (Python/Flask)**: 运行在 **Windows* 主机上。负责响应前端请求，读取预处理结果，并调用 AI 模型（LSTM/随机森林等）进行实时预测。
* **数据存储**:
* **静态文件**: `01_datapre/` 目录，存储 Spark 算好的聚类中心 (`center_data_sorted.json`) 及清洗后的业务数据。
* **模型文件**: `02_training/` 目录，存储训练好的 `.pkl` 或 `.h5` 等模型文件。



### 1.1 开发规范

* **接口协议**: HTTP / RESTful
* **数据格式**: JSON (Content-Type: application/json)
* **字符编码**: UTF-8
* **跨域处理**: 后端统一开启 CORS 支持前端调用。
* **端口**: 5000 | **Base URL**: http://localhost:5000/api
---

## 2. 统一响应格式 (Standard Response)

所有接口均返回统一的 JSON 数据结构：

```json
{
    "code": 200,          // 业务状态码 (200: 成功, 500: 服务器错误, 400: 参数错误)
    "msg": "success",     // 提示信息
    "data": { ... }       // 业务数据载荷
}

```

---
## 3. 认证模块

### 3.1 用户登录

**功能**: 用户登录，获取JWT token。
**URL**: `/auth/login`
**Method**: `POST`

**Request Body**:

```json
{
    "username": "admin",
    "password": "123456"
}
```

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "token": "abcdefghijklmnopqrstuvwxyz"
    }
}
```

---

## 4. 用户聚类分析模块 (Cluster Module)

该模块用于前端展示 K-Means 聚类算出的用户画像，数据来源于 Spark 离线计算产出的 JSON 文件。

### 4.1 获取聚类中心曲线

**功能**: 获取不同类别用户的全年负荷形态曲线（归一化后的数据），用于 ECharts 折线图展示。
**URL**: `/cluster/centers`
**Method**: `GET`

**Request Params**: 无

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "dates": ["2017/05/01", "2017/05/02", ...],  // X轴：日期序列
        "centers": [
            [0.12, 0.15, ...],  // 类别0 的365天曲线数据
            [0.45, 0.48, ...],  // 类别1 的365天曲线数据
            [0.05, 0.05, ...]   // 类别2 的365天曲线数据
        ],
        "counts": [605, 54, 341] // 各类别用户数量
    }
}

```

### 4.2 获取聚类统计分布

**功能**: 获取各类用户的数量占比及标签定义，用于 ECharts 饼图或仪表盘。
**URL**: `/cluster/stats`
**Method**: `GET`

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": [
        { "name": "中能耗常规型", "value": 341, "label_id": 0 },
        { "name": "低能耗平稳型", "value": 605, "label_id": 1 },
        { "name": "高能耗波动型", "value": 54, "label_id": 2 }
    ]
}

```

---

## 5. 行业用电预测模块 (Prediction Module)

该模块用于调用后端训练好的机器学习模型（RandomForest / LSTM），对特定行业的未来用电趋势进行预测。

### 5.1 获取行业列表

**功能**: 获取支持预测的行业分类列表（如：住宿餐饮、交通运输等），供前端下拉框选择。
**URL**: `/industry/list`
**Method**: `GET`

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": [
        { "id": "1001", "name": "住宿和餐饮业" },
        { "id": "1002", "name": "交通运输、仓储和邮政业" },
        { "id": "1003", "name": "批发和零售业" }
    ]
}

```

### 5.2 执行用电预测

**功能**: 提交行业 ID 和预测时间范围，调用后端 LSTM 模型返回预测结果。
**URL**: `/industry/predict`
**Method**: `POST`

**Request Body**:

```json
{
    "industry_id": "1001",
    "model_type": "lstm",    // 可选值: "lstm", "rf" (随机森林)
    "future_days": 30        // 预测未来多少天
}

```

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "dates": ["2018/05/01", "2018/05/02", ...], // 预测日期序列
        "values": [2500.5, 2610.2, ...],           // 预测电量值
        "trend_desc": "预计未来30天该行业用电量呈上升趋势，环比增长 5.2%。"
    }
}

```

### 5.3 获取行业分类及其数量

**功能**: 获取一级行业和二级行业的分组统计信息，用于 ECharts 双层嵌套饼图。
**URL**: `/industry/categories`
**Method**: `GET`

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "level1": [
            { "name": "住宿业", "count": 120 },
            { "name": "房地产业", "count": 85 },
            { "name": "道路运输业", "count": 200 }
        ],
        "level2": [
            { "name": "旅游饭店", "parent": "住宿业", "count": 80 },
            { "name": "房地产中介服务", "parent": "房地产业", "count": 45 },
            { "name": "道路货物运输", "parent": "道路运输业", "count": 150 }
        ]
    }
}
```

### 5.4 导入行业用电量CSV

**功能**: 上传宽表格式的CSV文件（每日用电量），自动转为长表存入数据库。
**URL**: `/industry/upload-csv`
**Method**: `POST`
**Content-Type**: `multipart/form-data`

**Request Body**:

| 字段名 | 类型 | 必填 | 说明 |
| ------ | ---- | --- | ---- |
| file | File | 是 | CSV文件（宽表格式，含 v2020_05_01 等日期列） |

**CSV文件格式要求**:

列头应包含维度列和日期列：
`elec_type_code, level1, trade_code, cons_sort_code, yc_id, cons_id, mp_id, start_date, v2020_05_01, v2020_05_02, ..., v2021_04_30`

**Response Example**:

```json
{
    "code": 200,
    "msg": "数据导入完成",
    "data": {
        "success": true,
        "total": 365000,
        "success_count": 364980,
        "error_count": 20,
        "date_columns": 366,
        "errors": ["行 15: 数据格式错误"]
    }
}
```

### 5.5 获取行业用电量时间序列

**功能**: 获取某行业按日聚合的用电量时间序列，用于面积图/折线图展示。支持多行业对比。
**URL**: `/industry/timeseries`
**Method**: `GET`

**Query Parameters**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| ------ | ---- | --- | ------ | ---- |
| level | int | 否 | 1 | 层级 (1=一级行业, 2=二级行业) |
| name | string | 是 | - | 行业名称，多个用逗号分隔 |
| start_date | string | 否 | - | 起始日期 (YYYY-MM-DD) |
| end_date | string | 否 | - | 结束日期 (YYYY-MM-DD) |

**单行业 Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "dates": ["2020-05-01", "2020-05-02", "2020-05-03"],
        "values": [72833.59, 53860.84, 51362.38],
        "name": "道路运输业",
        "level": 1
    }
}
```

**多行业 Response Example** (name=道路货物运输,公路旅客运输,道路运输辅助活动):

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "dates": ["2020-05-01", "2020-05-02", "2020-05-03"],
        "series": [
            { "name": "道路货物运输", "values": [30000, 28000, 27000] },
            { "name": "公路旅客运输", "values": [25000, 22000, 20000] },
            { "name": "道路运输辅助活动", "values": [17833, 13860, 14362] }
        ]
    }
}
```

---

## 6. 电力地图可视化模块 (Map Module)

该模块提供基于地理信息系统 (GIS) 的数据支持，结合 Leaflet 前端库展示用户分布。

### 6.1 获取用户坐标点集

**功能**: 获取所有用户的经纬度坐标及基础信息，用于在地图上渲染散点或热力图。
**URL**: `/map/points`
**Method**: `GET`

**Request Params**:

* `limit` (Optional): `int`, 限制返回点数量（默认 1000，防止前端卡顿）

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": [
        {
            "yc_id": "10001",
            "lat": 31.2304,       // 纬度 (userpoint_y)
            "lng": 121.4737,      // 经度 (userpoint_x)
            "type": "高能耗波动型", // 聚类结果标签
            "value": 4500.5       // 年用电量
        },
        ...
    ]
}


```

---

## 7. 用户数据管理模块 (Query Module)

### 7.1 获取用户列表（分页）

**功能**: 查询数据库中的用户数据列表，支持分页和关键词搜索。

**URL**: `/query/users`

**Method**: `GET`

**Query Parameters**:

| 参数名    | 类型   | 必填 | 默认值 | 说明                               |
| --------- | ------ | --- | ------ | ---------------------------------- |
| page      | int    | 否  | 1      | 页码（从1开始）                    |
| page_size | int    | 否  | 10     | 每页数量（1-100之间）              |
| keyword   | string | 否  | -      | 搜索关键词，支持用采ID和电表ID搜索 |

**Response Example**:

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "list": [
            {
                "id": 1,
                "yc_id": "10001479",
                "meter_id": "7351864548",
                "build_date": "2000-02-01 00:00:00",
                "trade_code": "城镇居民",
                "elec_type_code": "城镇居民生活用电",
                "cons_sort_code": "低压居民",
                "volt_code": "交流220V",
                "contract_cap": 3,
                "userpoint_x": 121.4737,
                "userpoint_y": 31.2304
            }
        ],
        "total": 1000,
        "page": 1,
        "page_size": 10,
        "total_pages": 100
    }
}
```

### 7.2 上传CSV文件导入用户数据

**功能**: 通过CSV文件批量导入用户数据到数据库。

**URL**: `/query/upload-csv`

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Request Body**:

| 字段名 | 类型 | 必填 | 说明              |
| ------ | ---- | --- | ----------------- |
| file   | File | 是  | CSV文件（.csv格式）|

**CSV文件格式要求**:

CSV文件应包含以下列头（英文或中文映射）：
`yc_id, meter_id, build_date, trade_code, elec_type_code, cons_sort_code, volt_code, contract_cap, userpoint_x, userpoint_y`

**Response Example**:

```json
{
    "code": 200,
    "msg": "数据导入完成",
    "data": {
        "success": true,
        "total": 1000,
        "success_count": 980,
        "error_count": 20,
        "errors": ["第15行: 用采id为空"]
    }
}
```

---

## 8. 错误码说明

| code | 说明                         |
| ---- | ---------------------------- |
| 200  | 请求成功                     |
| 400  | 参数错误                     |
| 401  | 未授权                       |
| 404  | 资源不存在                   |
| 500  | 服务器内部错误               |
