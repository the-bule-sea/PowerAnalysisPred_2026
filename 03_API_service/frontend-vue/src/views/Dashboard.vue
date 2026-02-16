<template>
  <MainLayout>
    <div class="dashboard-content">
      <!-- 欢迎卡片 -->
      <div class="welcome-card card">
        <h1>欢迎回来，管理员</h1>
        <p>今天是 {{ currentDate }}，系统运行正常。您可以通过左侧菜单访问各项分析功能。</p>
      </div>

      <!-- 核心指标概览 -->
      <div class="stats-grid">
        <div class="stat-card card">
          <div class="stat-icon bg-blue"></div>
          <div class="stat-info">
            <span class="label">接入用户总数</span>
            <span class="value">12,450</span>
            <span class="trend up">Total Users</span>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon bg-green"></div>
          <div class="stat-info">
            <span class="label">今日总用电量</span>
            <span class="value">845.2 MWh</span>
            <span class="trend down">Today's Consumption</span>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon bg-purple"></div>
          <div class="stat-info">
            <span class="label">预测模型准确率</span>
            <span class="value">96.8%</span>
            <span class="trend up">Model Accuracy</span>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon bg-orange"></div>
          <div class="stat-info">
            <span class="label">异常用电告警</span>
            <span class="value">23</span>
            <span class="trend down">Alerts</span>
          </div>
        </div>
      </div>

      <!-- 功能入口网格 -->
      <h2 class="section-title">快速入口</h2>
      <div class="features-grid">
        <div class="feature-card card" @click="$router.push('/cluster')">
          <div class="card-header">
            <h3>用户聚类分析</h3>
            <span class="arrow">→</span>
          </div>
          <p>基于K-Means算法的用户用电行为分类，洞察用户画像。</p>
          <div class="tags">
            <span class="tag">K-Means</span>
            <span class="tag">行为分析</span>
          </div>
        </div>
        
        <div class="feature-card card" @click="$router.push('/predict')">
          <div class="card-header">
            <h3>行业用电预测</h3>
            <span class="arrow">→</span>
          </div>
          <p>使用LSTM和随机森林模型，精准预测行业未来用电趋势。</p>
          <div class="tags">
            <span class="tag">LSTM</span>
            <span class="tag">Random Forest</span>
          </div>
        </div>
        
        <div class="feature-card card" @click="$router.push('/map')">
          <div class="card-header">
            <h3>电力地图可视化</h3>
            <span class="arrow">→</span>
          </div>
          <p>结合GIS地理信息系统，全景展示区域电力负荷分布。</p>
          <div class="tags">
            <span class="tag">GIS</span>
            <span class="tag">Leaflet</span>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { computed } from 'vue'
import MainLayout from '@/components/MainLayout.vue'

const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    weekday: 'long'
  })
})
</script>

<style scoped>
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.welcome-card {
  background: linear-gradient(120deg, #165DFF 0%, #722ED1 100%);
  color: white;
  border: none;
  padding: 32px;
}

.welcome-card h1 {
  font-size: 24px;
  margin-bottom: 8px;
  font-weight: 600;
}

.welcome-card p {
  opacity: 0.9;
  font-size: 14px;
}

/* 统计卡片样式 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 16px;
}

.bg-blue { background: rgba(22, 93, 255, 0.1); color: #165DFF; }
.bg-green { background: rgba(0, 180, 42, 0.1); color: #00B42A; }
.bg-purple { background: rgba(114, 46, 209, 0.1); color: #722ED1; }
.bg-orange { background: rgba(255, 125, 0, 0.1); color: #FF7D00; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-info .label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-info .value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-info .trend {
  font-size: 12px;
  margin-top: 2px;
  opacity: 0.8;
}

/* 功能卡片样式 */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 8px;
  padding-left: 8px;
  border-left: 4px solid var(--primary-color);
  line-height: 1.2;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 180px;
}

.feature-card:hover .arrow {
  transform: translateX(4px);
  color: var(--primary-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.arrow {
  font-size: 20px;
  color: var(--text-placeholder);
  transition: all 0.3s;
}

.feature-card p {
  color: var(--text-regular);
  font-size: 14px;
  margin-bottom: 24px;
  line-height: 1.6;
}

.tags {
  display: flex;
  gap: 8px;
}

.tag {
  background: var(--bg-body);
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
