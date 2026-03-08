<template>
  <MainLayout>
    <div class="map-page">

      <!-- 顶部工具栏 -->
      <div class="map-toolbar">
        <div class="toolbar-left">
          <div class="filter-label">用户分类筛选</div>
          <div class="filter-group">
            <button
              v-for="f in filters"
              :key="f.value"
              class="filter-btn"
              :class="{ active: activeFilter === f.value }"
              :style="activeFilter === f.value ? { borderColor: f.color, color: f.color, background: f.color + '1a' } : {}"
              @click="setFilter(f.value)"
            >
              <span class="filter-dot" :style="{ background: f.color }"></span>
              {{ f.label }}
            </button>
          </div>
        </div>
        <div class="toolbar-right">
          <!-- 地图类型切换 -->
          <div class="map-type-switcher">
            <button
              class="type-btn"
              :class="{ active: mapType === 'normal' }"
              @click="setMapType('normal')"
            >普通地图</button>
            <button
              class="type-btn"
              :class="{ active: mapType === 'satellite' }"
              @click="setMapType('satellite')"
            >卫星地图</button>
          </div>
          <span class="point-count">
            共显示 <strong>{{ displayCount }}</strong> 个用户
          </span>
        </div>
      </div>

      <!-- 地图主体 -->
      <div class="map-card">
        <!-- 地图容器 -->
        <div id="amap-container" ref="mapContainer"></div>

        <!-- 加载状态蒙层 -->
        <div class="map-overlay" v-if="mapStatus !== 'ready'">
          <div class="overlay-content">
            <div v-if="mapStatus === 'loading'" class="loading-spinner"></div>
            <div v-if="mapStatus === 'error'" class="error-icon">!</div>
            <p>{{ statusText }}</p>
            <p v-if="mapStatus === 'error'" class="error-tip">
              请在 Map.vue 中将 <code>YOUR_AMAP_KEY</code> 替换为有效的高德 Web JS API 密钥
            </p>
          </div>
        </div>

        <!-- 右下角图例 -->
        <div class="map-legend" v-if="mapStatus === 'ready'">
          <div class="legend-title">用户聚类分布</div>
          <div v-for="f in clusterFilters" :key="f.value" class="legend-item">
            <span class="legend-dot" :style="{ background: f.color }"></span>
            <span class="legend-label">{{ f.label }}</span>
          </div>
        </div>
      </div>

    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { getMapPoints } from '@/api/map'

// ===== 配置 =====
const AMAP_KEY = '6a951d46f61fb7099c2974de8c55270c'
const AMAP_VERSION = '2.0'

// 上海中心坐标
const SHANGHAI_CENTER = [121.4737, 31.2304]

// ===== 聚类筛选配置 =====
const filters = [
  { value: 'all',  label: '全部用户',   color: '#165DFF' },
  { value: '1',    label: '低能耗平稳型', color: '#00b42a' },
  { value: '0',    label: '中能耗常规型', color: '#ff7d00' },
  { value: '2',    label: '高能耗波动型', color: '#f53f3f' },
]
const clusterFilters = filters.slice(1) // 图例不需要"全部"

// 聚类颜色映射
const CLUSTER_COLORS = {
  0: '#ff7d00',  // 中能耗：橙色
  1: '#00b42a',  // 低能耗：绿色
  2: '#f53f3f',  // 高能耗：红色
}

// ===== 状态 =====
const mapContainer = ref(null)
const mapStatus = ref('loading')   // loading | ready | error
const activeFilter = ref('all')
const mapType = ref('normal')      // normal | satellite
const allPoints = ref([])          // 原始数据
const markers = ref([])            // AMap Marker 实例
let mapInstance = null
let satelliteLayer = null
let roadNetLayer = null

const statusText = computed(() => {
  if (mapStatus.value === 'loading') return '地图加载中...'
  if (mapStatus.value === 'error')   return '地图加载失败'
  return ''
})

const displayCount = computed(() => {
  return markers.value.length
})

// ===== 动态加载高德 JS API =====
function loadAmapScript() {
  return new Promise((resolve, reject) => {
    // 避免重复加载
    if (window.AMap) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=${AMAP_VERSION}&key=${AMAP_KEY}`
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('高德地图 API 脚本加载失败，请检查 Key 是否正确'))
    document.head.appendChild(script)
  })
}

// ===== 初始化地图 =====
function initMap() {
  mapInstance = new window.AMap.Map('amap-container', {
    center: SHANGHAI_CENTER,
    zoom: 11,
    mapStyle: 'amap://styles/whitesmoke',
  })
  // 预创建卫星和路网图层（不加入地图，切换时按需 add/remove）
  satelliteLayer = new window.AMap.TileLayer.Satellite()
  roadNetLayer   = new window.AMap.TileLayer.RoadNet()
  mapInstance.on('complete', () => {
    mapStatus.value = 'ready'
    fetchAndRender()
  })
}

// ===== 地图类型切换 =====
function setMapType(type) {
  if (!mapInstance || mapType.value === type) return
  mapType.value = type
  if (type === 'satellite') {
    // 叠加卫星影像 + 路网标注（卫星瓦片会覆盖底图）
    mapInstance.add([satelliteLayer, roadNetLayer])
  } else {
    // 移除卫星和路网图层，原始 whitesmoke 底图自动露出
    mapInstance.remove([satelliteLayer, roadNetLayer])
  }
}

// ===== 拉取后端数据 =====
async function fetchAndRender(clusterType = null) {
  try {
    const params = { limit: 1000 }
    if (clusterType !== null) params.cluster_type = clusterType

    const res = await getMapPoints(params)
    if (Array.isArray(res.data)) {
      allPoints.value = res.data
      renderMarkers(res.data)
    } else {
      console.warn('地图数据返回异常:', res)
    }
  } catch (e) {
    console.warn('地图数据拉取失败（后端可能未启动）:', e.message)
  }
}

// ===== 渲染打点 =====
function renderMarkers(points) {
  // 清空旧标记
  clearMarkers()

  const newMarkers = points.map(p => {
    const color = CLUSTER_COLORS[p.cluster_type] ?? '#86909c'
    const marker = new window.AMap.CircleMarker({
      center: new window.AMap.LngLat(p.lng, p.lat),
      radius: 5,
      fillColor: color,
      fillOpacity: 0.85,
      strokeColor: '#fff',
      strokeWeight: 1,
      cursor: 'pointer',
    })
    // 信息窗体
    marker.on('click', () => {
      const infoWindow = new window.AMap.InfoWindow({
        content: `
          <div style="font-size:13px;line-height:1.8;padding:4px 6px;">
            <b>用采 ID：</b>${p.yc_id}<br>
            <b>用户分类：</b>${clusterLabel(p.cluster_type)}<br>
            <b>年用电量：</b>${p.value != null ? p.value.toFixed(1) + ' kWh' : '暂无'}
          </div>
        `,
        offset: new window.AMap.Pixel(0, -12),
      })
      infoWindow.open(mapInstance, new window.AMap.LngLat(p.lng, p.lat))
    })
    marker.setMap(mapInstance)
    return marker
  })
  markers.value = newMarkers
}

function clusterLabel(type) {
  const map = { 0: '中能耗常规型', 1: '低能耗平稳型', 2: '高能耗波动型' }
  return map[type] ?? '未分类'
}

function clearMarkers() {
  markers.value.forEach(m => m.setMap(null))
  markers.value = []
}

// ===== 筛选切换（重新请求后端） =====
function setFilter(val) {
  activeFilter.value = val
  if (!mapInstance) return
  const clusterType = val === 'all' ? null : parseInt(val)
  fetchAndRender(clusterType)
}

// ===== 生命周期 =====
onMounted(async () => {
  try {
    await loadAmapScript()
    initMap()
  } catch (e) {
    mapStatus.value = 'error'
    console.error(e)
  }
})

onUnmounted(() => {
  clearMarkers()
  mapInstance?.destroy()
  mapInstance = null
})
</script>

<style scoped>
.map-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== 工具栏 ===== */
.map-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: var(--radius-md, 8px);
  padding: 12px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-label {
  font-size: 13px;
  color: var(--text-secondary, #86909c);
  white-space: nowrap;
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border: 1px solid var(--border-color, #e5e6eb);
  background: #fff;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-regular, #4e5969);
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #165DFF;
  color: #165DFF;
}

.filter-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary, #86909c);
}

.toolbar-right strong {
  color: var(--text-primary, #1d2129);
  font-weight: 600;
}

/* ===== 地图类型切换 ===== */
.map-type-switcher {
  display: flex;
  border: 1px solid var(--border-color, #e5e6eb);
  border-radius: 6px;
  overflow: hidden;
}

.type-btn {
  padding: 5px 14px;
  font-size: 13px;
  background: #fff;
  border: none;
  cursor: pointer;
  color: var(--text-regular, #4e5969);
  transition: background 0.2s, color 0.2s;
  white-space: nowrap;
}

.type-btn + .type-btn {
  border-left: 1px solid var(--border-color, #e5e6eb);
}

.type-btn:hover {
  background: #f2f3f5;
}

.type-btn.active {
  background: #165DFF;
  color: #fff;
}

/* ===== 地图容器 ===== */
.map-card {
  flex: 1;
  min-height: 0;
  position: relative;
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

#amap-container {
  width: 100%;
  height: 100%;
}

/* ===== 加载蒙层 ===== */
.map-overlay {
  position: absolute;
  inset: 0;
  background: #1a1f2e;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.overlay-content {
  text-align: center;
  color: #c9cdd4;
}

.overlay-content p {
  margin-top: 12px;
  font-size: 14px;
}

.error-tip {
  margin-top: 8px !important;
  font-size: 12px !important;
  color: #86909c;
  max-width: 300px;
  line-height: 1.6;
}

.error-tip code {
  background: rgba(255,255,255,0.1);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: monospace;
  color: #ff7d00;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #165DFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

.error-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f53f3f;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== 图例 ===== */
.map-legend {
  position: absolute;
  right: 16px;
  bottom: 32px;
  background: rgba(20, 25, 40, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  padding: 12px 16px;
  z-index: 9;
  border: 1px solid rgba(255,255,255,0.1);
}

.legend-title {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  color: rgba(255,255,255,0.85);
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
