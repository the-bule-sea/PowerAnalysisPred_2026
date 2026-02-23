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
            <select class="form-select" v-model="selectedIndustry">
              <option v-for="item in industryList" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          
          <div class="form-item">
            <label>预测模型</label>
            <div class="radio-group">
              <label 
                class="radio-item" 
                :class="{ active: modelType === 'lstm' }" 
                @click="modelType = 'lstm'"
              >LSTM 神经网络</label>
              <label 
                class="radio-item" 
                :class="{ active: modelType === 'rf' }" 
                @click="modelType = 'rf'"
              >随机森林</label>
            </div>
          </div>
          
          <div class="form-item">
            <label>预测天数</label>
            <div class="days-row">
              <input type="number" v-model.number="futureDays" class="days-input" min="1" max="90" />
              <span class="unit">天</span>
            </div>
          </div>
          
          <button class="btn btn-primary start-btn" @click="runPredict" :disabled="isPredicting">
            {{ isPredicting ? '预测中...' : '开始预测' }}
          </button>
        </div>
      </div>

      <!-- 结果展示区 -->
      <div class="result-section card">
        <div class="result-header">
          <h3>预测结果概览</h3>
          <div v-if="trendDesc" class="trend-indicator" :class="trendDirection">
            <span>{{ trendDesc }}</span>
            <span class="arrow">{{ trendDirection === 'up' ? '↑' : '↓' }}</span>
          </div>
        </div>
        
        <div class="chart-area">
          <!-- 无数据占位 -->
          <div v-if="!hasResult" class="chart-placeholder">
            <span>请选择参数后点击"开始预测"</span>
          </div>
          <!-- ECharts 图表 -->
          <div v-show="hasResult" ref="chartRef" class="chart-container"></div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted, shallowRef, nextTick } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
const chart = shallowRef(null)

const industryList = ref([])
const selectedIndustry = ref('')
const modelType = ref('lstm')
const futureDays = ref(30)
const isPredicting = ref(false)
const hasResult = ref(false)
const trendDesc = ref('')
const trendDirection = ref('up')

// 1. 获取行业列表 (5.1)
const fetchIndustryList = async () => {
  try {
    const res = await fetch('http://localhost:5000/api/industry/list')
    const json = await res.json()
    if (json.code === 200 && json.data.length > 0) {
      industryList.value = json.data
      selectedIndustry.value = json.data[0].id
    }
  } catch (error) {
    console.error('获取行业列表失败', error)
    // 降级 Mock
    industryList.value = [
      { id: '住宿业', name: '住宿业' },
      { id: '道路运输业', name: '道路运输业' }
    ]
    selectedIndustry.value = '住宿业'
  }
}

// 2. 执行预测 (5.2)
const runPredict = async () => {
  isPredicting.value = true
  hasResult.value = false
  trendDesc.value = ''

  try {
    const res = await fetch('http://localhost:5000/api/industry/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        industry_id: selectedIndustry.value,
        model_type: modelType.value,
        future_days: futureDays.value
      })
    })
    const json = await res.json()

    if (json.code === 200 && json.data) {
      const data = json.data
      trendDesc.value = data.trend_desc
      trendDirection.value = data.trend_desc.includes('上升') ? 'up' : 'down'
      hasResult.value = true
      nextTick(() => {
        renderChart(data)
      })
    } else {
      alert(`预测失败: ${json.msg}`)
    }
  } catch (error) {
    alert('请求失败，请检查后端是否已启动且已导入数据')
  } finally {
    isPredicting.value = false
  }
}

// 3. 渲染 ECharts 图表
const renderChart = (data) => {
  if (!chart.value && chartRef.value) {
    chart.value = echarts.init(chartRef.value)
  }
  if (!chart.value) return

  const actualDates = data.actual_dates || []
  const actualValues = data.actual_values || []
  const predictDates = data.predict_dates || []
  const predictValues = data.predict_values || []

  // 合并历史 + 预测日期轴并去重排序
  const allDates = [...new Set([...actualDates, ...predictDates])].sort()

  const actualMap = {}
  actualDates.forEach((d, i) => actualMap[d] = actualValues[i])
  const predictMap = {}
  predictDates.forEach((d, i) => predictMap[d] = predictValues[i])

  // 生成对齐后的 Y 轴数据序列
  const finalActualSeries = allDates.map(d => (actualMap[d] !== undefined ? actualMap[d] : null))
  const finalPredictSeries = allDates.map(d => (predictMap[d] !== undefined ? predictMap[d] : null))

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史用电量', 'LSTM 预测用电量'], icon: 'circle', top: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: allDates },
    yAxis: { type: 'value', name: '用电量 (Wh)' },
    dataZoom: [
      { type: 'slider', show: true, xAxisIndex: [0], bottom: 0, start: 0, end: 100 }
    ],
    series: [
      {
        name: '历史用电量',
        type: 'line',
        data: finalActualSeries,
        smooth: true,
        itemStyle: { color: '#91cc75' },  // 浅绿色
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(145, 204, 117, 0.5)' },
            { offset: 1, color: 'rgba(145, 204, 117, 0.1)' }
          ])
        }
      },
      {
        name: 'LSTM 预测用电量',
        type: 'line',
        data: finalPredictSeries,
        smooth: true,
        itemStyle: { color: '#7b9ce1' }, // 蓝紫色
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(123, 156, 225, 0.5)' },
            { offset: 1, color: 'rgba(123, 156, 225, 0.1)' }
          ])
        }
      }
    ]
  }
  chart.value.setOption(option, true)
}

const handleResize = () => {
  chart.value?.resize()
}

onMounted(() => {
  fetchIndustryList()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart.value?.dispose()
})
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
  outline: none;
  background: #fff;
}

.days-input {
  width: 100px;
  min-width: unset;
}

.days-row {
  display: flex;
  align-items: center;
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
  transition: all 0.2s;
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

.result-section {
  padding: 24px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.result-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
  font-size: 13px;
}

.trend-indicator.up {
  background: rgba(0, 180, 42, 0.1);
  color: var(--success-color);
}

.trend-indicator.down {
  background: rgba(245, 63, 63, 0.1);
  color: #f53f3f;
}

.chart-placeholder {
  height: 400px;
  background: var(--bg-body);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
}

.chart-container {
  height: 400px;
  width: 100%;
}
</style>
