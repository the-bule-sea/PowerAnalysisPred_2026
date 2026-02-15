# guide
## project name
用电行为分析与行业用电预测平台设计及实现
## project requirement
本课题旨在设计并开发一款电力数据可视化平台，核心聚焦用户行为分析与行业用电预测两大核心任务。
平台以电力用户基础数据、日冻结电量数据及行业用电数据为支撑，通过K-Means聚类算法挖掘用户用电特征，实现用户群体精准细分;采用随机森林与长短期记忆神经网络构建多模型预测体系，提升行业用电趋势预测的准确性;
基于前后端分离架构与MVC设计模式，整合查询界面、用户聚类分析、电力地图可视化、行业景气评估四大功能模块，通过 ECharts图表联动、Leaflet地理信息展示等技术，实现数据的多维度、交五式呈现。
## project structure
01_datapre | 数据预处理
02_training | 模型训练
03_API_service | API服务
    -backend | Flask后端
    -frontend-vue | Vue前端

**具体要求**
1. Flask做后端，要求api分层，api参考目录下的api_design.md
2. vue做前端，要求vue3+js

**数据库设计**
```
根据用户数据字段建表，yc_id作为主键，该数据字段如表4-1所示。
表 4-1 用户数据字段
字段	| 含义
yc_id	| 用采id（和电量id相等）
meter_id	| 表号
build_date	| 立户日期
trade_code	| 行业分类
elec_type_code	| 用电类型
cons_sort_code	| 用电分类
volt_code	| 供电电压
contract_cap	| 合同容量
userpoint_x	| 经度
userpoint_y	| 纬度

根据用户日冻结电量数据建表，自增序号作为主键，数据量：1000条用户的一年的日冻结电量，数据字段如表4-2所示。
表 4-2 用电查询-用户日冻结电量数据字段
字段	| 含义
yc_id	| 用采id（和用户数据的yc_id相等）
sum	| 一年内不为null的电量数据条数
cluster	| 聚类类别
pap_r	| 用户电量（单位：千瓦时，下同）
pap_r1	| 用电峰值
pap_r2	| 用电谷值
data_date	| 日期

根据行业数据建表，并存入数据库，自增序号作为主键，数据量：1000条行业的一年的日冻结电量，时间跨度是：2017-05-01~2018-04-30，该数据的数据字段如表4-3所示。
表 4-3 行业数据字段
字段	| 含义
elec_type_code	| 用电类型
level1	| 一级行业（道路运输业、房地产业、住宿业）
trade_code	| 所属行业、二级行业
（道路运输辅助活动、房地产中介服务、公路旅客运输、道路货物运输、旅游饭店）
cons_sort_code	| 用户分类
yc_id	| 用采id
cons_id	| 用户id
sum	| 年总用电量
avg	| 年平均用电量
```