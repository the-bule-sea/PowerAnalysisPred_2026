<template>
  <MainLayout>
    <div class="page-header">
      <div class="header-content">
        <h2>用户用电行为聚类分析</h2>
        <p>基于K-Means算法（K=3），将用户群体划分为不同用电模式，辅助差异化服务</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="loadData" :disabled="loading">
          {{ loading ? '加载中...' : '刷新数据' }}
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card card" v-for="stat in stats" :key="stat.label_id">
        <div class="stat-label">{{ stat.name }}</div>
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-bar" :style="{ width: (stat.value / totalUsers * 100) + '%', background: colors[stat.label_id] }"></div>
      </div>
    </div>

    <!-- 图表容器 -->
    <div class="charts-container">
      <div class="chart-wrapper card">
        <div class="chart-header">
          <h3>聚类中心形态曲线</h3>
          <p>展示三种典型用户群的年度日用电量归一化曲线</p>
        </div>
        <div ref="lineChartRef" class="chart-box"></div>
      </div>
      
      <div class="chart-wrapper card">
        <div class="chart-header">
          <h3>用户分布占比</h3>
          <p>各类别用户数量统计</p>
        </div>
        <div ref="pieChartRef" class="chart-box pie-chart"></div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import MainLayout from '@/components/MainLayout.vue'
import { getClusterCenters, getClusterStats } from '@/api/cluster'

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const stats = ref([])
const loading = ref(false)
const centers = ref(null)

// 定义颜色与参考图一致
const colors = ['#FF6B6B', '#4ECDC4', '#9B59B6']
const classNames = ['Class 0', 'Class 1', 'Class 2']

const totalUsers = computed(() => {
  return stats.value.reduce((sum, s) => sum + s.value, 0)
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行请求两个接口
    const [centersRes, statsRes] = await Promise.all([
      getClusterCenters(),
      getClusterStats()
    ])
    
    centers.value = centersRes.data
    stats.value = statsRes.data
    
    // 渲染图表
    renderLineChart()
    renderPieChart()
  } catch (error) {
    console.error('加载数据失败:', error)
    alert('加载聚类数据失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

// 渲染折线图
const renderLineChart = () => {
  if (!lineChartRef.value || !centers.value) return
  
  const chart = echarts.init(lineChartRef.value)
  
  const { dates, centers: centerData, counts } = centers.value
  
  const series = centerData.map((data, index) => ({
    name: `${classNames[index]} (Count: ${counts[index]})`,
    type: 'line',
    data: data,
    smooth: true,
    lineStyle: {
      width: 2,
      color: colors[index]
    },
    itemStyle: {
      color: colors[index]
    },
    showSymbol: false
  }))
  
  const option = {
    title: {
      text: '用户群体用电行为模式聚类分析 (K=3)',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'line'
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 35,
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLabel: {
        interval: 30,
        rotate: 0,
        fontSize: 11
      },
      name: '日期',
      nameLocation: 'center',
      nameGap: 35
    },
    yAxis: {
      type: 'value',
      name: '归一化用电量 (0~1)',
      nameLocation: 'center',
      nameGap: 45,
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: series
  }
  
  chart.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => chart.resize())
}

// 渲染饼图
const renderPieChart = () => {
  if (!pieChartRef.value || !stats.value.length) return
  
  const chart = echarts.init(pieChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center'
    },
    series: [
      {
        name: '用户分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: stats.value.map((item, index) => ({
          value: item.value,
          name: item.name,
          itemStyle: {
            color: colors[index]
          }
        }))
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-content h2 {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.header-content p {
  color: var(--text-secondary);
  font-size: 14px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  padding: 20px;
  overflow: hidden;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  transition: width 0.5s ease;
}

.charts-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.chart-wrapper {
  padding: 24px;
}

.chart-header {
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.chart-header p {
  font-size: 13px;
  color: var(--text-secondary);
}

.chart-box {
  width: 100%;
  height: 500px;
}

.pie-chart {
  height: 400px;
}
</style>
