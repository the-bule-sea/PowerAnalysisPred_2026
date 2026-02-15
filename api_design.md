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


