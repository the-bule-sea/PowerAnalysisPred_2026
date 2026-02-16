<template>
  <MainLayout>
    <div class="predict-page">
      <!-- 顶部控制栏 -->
      <div class="control-panel card">
        <div class="title-row">
          <h3>行业预测参数设置</h3>
          <span class="desc">选择行业与预测模型，生成未来趋势。</span>
        </div>
        
        <div class="form-row">
          <div class="form-item">
            <label>行业分类</label>
            <select class="form-select">
              <option>住宿和餐饮业</option>
              <option>批发和零售业</option>
            </select>
          </div>
          
          <div class="form-item">
            <label>预测模型</label>
            <div class="radio-group">
              <label class="radio-item active">LSTM 神经网络</label>
              <label class="radio-item">随机森林</label>
            </div>
          </div>
          
          <div class="form-item">
            <label>预测天数</label>
            <input type="number" value="30" class="days-input" />
            <span class="unit">天</span>
          </div>
          
          <button class="btn btn-primary start-btn">开始预测</button>
        </div>
      </div>

      <!-- 结果展示区 -->
      <div class="result-section card">
        <div class="result-header">
          <h3>预测结果概览</h3>
          <div class="trend-indicator up">
            <span>环比增长预计 +5.2%</span>
            <span class="arrow">↑</span>
          </div>
        </div>
        
        <div class="chart-area">
          <div class="chart-placeholder">
            <span>图表区域：历史数据与预测曲线对比</span>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import MainLayout from '@/components/MainLayout.vue'
</script>

<style scoped>
.predict-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.control-panel {
  padding: 24px;
}

.title-row {
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 16px;
}

.title-row h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.form-row {
  display: flex;
  align-items: flex-end;
  gap: 24px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 14px;
  color: var(--text-regular);
}

.form-select, .days-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  min-width: 200px;
}

.days-input {
  width: 100px;
  min-width: unset;
}

.unit {
  margin-left: 8px;
  color: var(--text-secondary);
}

.radio-group {
  display: flex;
  gap: 12px;
}

.radio-item {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-regular);
}

.radio-item.active {
  background: rgba(22, 93, 255, 0.1);
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.start-btn {
  margin-left: auto;
  padding: 10px 24px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: rgba(0, 180, 42, 0.1);
  color: var(--success-color);
  border-radius: 12px;
  font-weight: 500;
  font-size: 13px;
}

.chart-placeholder {
  height: 400px;
  background: var(--bg-body);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
  border: 1px dashed var(--border-color);
}
</style>
