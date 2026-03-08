<template>
  <MainLayout>
    <div class="industry-page">
      <!-- 顶部操作栏 -->
      <div class="action-bar card">
        <div>
          <h3>行业分类与数据管理</h3>
          <p class="desc">全景展示不同行业的用电分布及历史趋势趋势</p>
        </div>
        <div class="actions">
          <input type="file" ref="csvFileRef" accept=".csv" style="display: none" @change="handleFileUpload">
          <button class="btn btn-secondary" @click="handleClearData" :disabled="isUploading" style="margin-right: 12px;">
            清空数据
          </button>
          <button class="btn btn-primary" @click="triggerUpload" :disabled="isUploading">
            {{ isUploading ? '导入中...' : '导入 CSV 数据' }}
          </button>
        </div>
      </div>

      <!-- 图表区：分类饼图 -->
      <div class="chart-card card">
        <h3 class="chart-title">行业分布及其数量</h3>
        <div ref="pieChartRef" class="chart-container pie-container"></div>
      </div>

      <!-- 图表区：一级行业用电时序 -->
      <div class="chart-card card">
        <div class="card-header">
          <div class="header-left">
            <span class="tag">一级</span>
            <h3 class="chart-title">一级行业</h3>
          </div>
          <div class="header-right">
            <select v-model="selectedLevel1" class="form-select" @change="handleLevel1Change">
              <option v-for="item in level1Options" :key="item" :value="item">{{ item }}</option>
            </select>
          </div>
        </div>
        <div ref="lineChart1Ref" class="chart-container line-container"></div>
      </div>

      <!-- 图表区：二级行业用电时序 -->
      <div class="chart-card card" v-if="level2Options.length">
        <div class="card-header">
          <div class="header-left">
            <span class="tag">二级</span>
            <h3 class="chart-title">二级行业</h3>
          </div>
        </div>
        <div ref="lineChart2Ref" class="chart-container line-container"></div>
      </div>

    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted, shallowRef, nextTick } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import * as echarts from 'echarts'
import {
  getIndustryCategories,
  getIndustryTimeseries,
  uploadIndustryCsv,
  clearIndustryData
} from '@/api/industry'

const pieChartRef = ref(null)
const lineChart1Ref = ref(null)
const lineChart2Ref = ref(null)

const pieChart = shallowRef(null)
const lineChart1 = shallowRef(null)
const lineChart2 = shallowRef(null)

const csvFileRef = ref(null)
const isUploading = ref(false)

const level1Options = ref([])
const selectedLevel1 = ref('道路运输业')
const level2Options = ref([])
const allCategories = ref({ level1: [], level2: [] })

// 初始化 ECharts
const initCharts = () => {
  if (pieChartRef.value && !pieChart.value) pieChart.value = echarts.init(pieChartRef.value)
  if (lineChart1Ref.value && !lineChart1.value) lineChart1.value = echarts.init(lineChart1Ref.value)
  if (lineChart2Ref.value && !lineChart2.value) lineChart2.value = echarts.init(lineChart2Ref.value)
}

// 获取行业分类数据
const fetchCategories = async () => {
  try {
    const res = await getIndustryCategories()
    if (res.data.level1.length > 0) {
      allCategories.value = res.data
      level1Options.value = res.data.level1.map(item => item.name)
      if (!level1Options.value.includes(selectedLevel1.value)) {
        selectedLevel1.value = level1Options.value[0]
      }
      renderPieChart()
      handleLevel1Change()
    } else {
      renderMockPieChart()
    }
  } catch (error) {
    console.error('API 失败，使用 Mock 数据', error)
    renderMockPieChart()
    handleLevel1Change()
  }
}

const renderMockPieChart = () => {
  const mockLevel1 = [
    { name: '房地产业', value: 85 },
    { name: '道路运输业', value: 200 },
    { name: '住宿业', value: 120 }
  ]
  const mockLevel2 = [
    { name: '房地产中介服务', value: 45 },
    { name: '道路运输辅助活动', value: 60 },
    { name: '道路货物运输', value: 100 },
    { name: '公路旅客运输', value: 40 },
    { name: '旅游饭店', value: 120 }
  ]
  level1Options.value = ['房地产业', '道路运输业', '住宿业']
  allCategories.value = { level1: mockLevel1, level2: mockLevel2 }
  selectedLevel1.value = '道路运输业'

  const option = getPieOption(mockLevel1, mockLevel2)
  pieChart.value?.setOption(option)
}

const renderPieChart = () => {
  const l1 = allCategories.value.level1.map(i => ({ name: i.name, value: i.count }))
  const l2 = allCategories.value.level2.map(i => ({ name: i.name, value: i.count }))
  pieChart.value?.setOption(getPieOption(l1, l2))
}

const getPieOption = (level1, level2) => {
  const legendData = level2.map(i => i.name)
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      type: 'scroll',
      top: 0,
      data: legendData,
      icon: 'roundRect'
    },
    color: ['#A063C1', '#72BCDE', '#4FAD73', '#FF8F54', '#EC6A6B', '#5A7CE2'],
    series: [
      {
        name: '一级行业',
        type: 'pie',
        radius: [0, '35%'],
        label: { position: 'inner', fontSize: 13, color: '#fff', formatter: '{b}' },
        itemStyle: { borderColor: '#fff', borderWidth: 1 },
        data: level1
      },
      {
        name: '二级行业',
        type: 'pie',
        radius: ['45%', '65%'],
        label: {
          formatter: '{b}',
          color: '#666'
        },
        itemStyle: { borderColor: '#fff', borderWidth: 1 },
        data: level2
      }
    ]
  }
}

const handleLevel1Change = async () => {
  const children = allCategories.value.level2.filter(i => i.parent === selectedLevel1.value || level1Options.value.length === 3)
  level2Options.value = children.map(i => i.name)

  try {
    const res = await getIndustryTimeseries(1, selectedLevel1.value)
    if (res.data.dates) {
      renderLineChart1(res.data.dates, res.data.values)
    } else {
      renderMockLineChart1()
    }
  } catch (error) {
    renderMockLineChart1()
  }

  if (level2Options.value.length > 0) {
    nextTick(() => {
      initCharts()
      fetchLevel2Data()
    })
  }
}

const fetchLevel2Data = async () => {
  try {
    const names = level2Options.value.join(',')
    const res = await getIndustryTimeseries(2, names)
    if (res.data.series) {
      renderLineChart2(res.data.dates, res.data.series)
    } else {
      renderMockLineChart2()
    }
  } catch(error) {
    renderMockLineChart2()
  }
}

const renderMockLineChart1 = () => {
  const dates = Array.from({length: 45}, (_, i) => `2020-05-${String(i+1).padStart(2,'0')}`)
  const values = Array.from({length: 45}, () => 60 + Math.random() * 50)
  renderLineChart1(dates, values)
}

const renderLineChart1 = (dates, values) => {
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: [selectedLevel1.value], icon: 'circle', right: '10%' },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: { type: 'value' },
    dataZoom: [
      { type: 'slider', show: true, xAxisIndex: [0], bottom: 0, start: 0, end: 30 }
    ],
    series: [
      {
        name: selectedLevel1.value,
        type: 'line',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(123, 156, 225, 0.5)' },
            { offset: 1, color: 'rgba(123, 156, 225, 0)' }
          ])
        },
        itemStyle: { color: '#7b9ce1' },
        smooth: true,
        data: values
      }
    ]
  }
  lineChart1.value?.setOption(option)
}

const renderMockLineChart2 = () => {
  const dates = Array.from({length: 45}, (_, i) => `2020-05-${String(i+1).padStart(2,'0')}`)
  const mockSeriesNames = level2Options.value.length ? level2Options.value : ['道路运输辅助活动', '公路旅客运输', '道路货物运输']
  
  const series = mockSeriesNames.map(name => ({
    name,
    values: Array.from({length: 45}, () => 30 + Math.random() * 20)
  }))
  renderLineChart2(dates, series)
}

const renderLineChart2 = (dates, seriesDataList) => {
  const colorPalette = ['#F5C448', '#86CB72', '#7b9ce1', '#A063C1', '#EC6A6B']
  const series = seriesDataList.map((s, idx) => ({
    name: s.name,
    type: 'line',
    stack: 'Total',
    areaStyle: {},
    smooth: true,
    itemStyle: { color: colorPalette[idx % colorPalette.length] },
    data: s.values
  }))

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: seriesDataList.map(s => s.name),
      icon: 'circle',
      top: 0
    },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: { type: 'value' },
    dataZoom: [
      { type: 'slider', show: true, xAxisIndex: [0], bottom: 0, start: 0, end: 30 }
    ],
    series: series
  }
  lineChart2.value?.setOption(option)
}

const triggerUpload = () => {
  csvFileRef.value.click()
}

const handleClearData = async () => {
  if (!confirm('确定要清空所有已导入的一级和二级行业用电数据吗？此操作不可撤销。')) return

  try {
    await clearIndustryData()
    alert('数据已成功清空')
    fetchCategories()
  } catch (error) {
    alert(`清空失败: ${error.message || '请检查后端服务是否已启动'}`)
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  isUploading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await uploadIndustryCsv(formData)
    alert(`导入成功！共处理 ${res.data.total} 行，成功 ${res.data.success_count} 行。`)
    fetchCategories()
  } catch (error) {
    alert(`导入失败: ${error.message || '请检查网络或后端状态'}`)
  } finally {
    isUploading.value = false
    event.target.value = ''
  }
}

const handleResize = () => {
  pieChart.value?.resize()
  lineChart1.value?.resize()
  lineChart2.value?.resize()
}

onMounted(() => {
  initCharts()
  fetchCategories()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  pieChart.value?.dispose()
  lineChart1.value?.dispose()
  lineChart2.value?.dispose()
})
</script>

<style scoped>
.industry-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
}

.action-bar h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.chart-card {
  padding: 24px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--bg-body);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-secondary);
}

.header-left h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.form-select {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  outline: none;
  background: #fff;
  cursor: pointer;
}

.pie-container {
  height: 480px;
  width: 100%;
}

.line-container {
  height: 380px;
  width: 100%;
}
</style>
