<template>
  <MainLayout>
    <div class="map-page-wrapper">
      <div class="map-toolbar">
        <input type="text" placeholder="搜索区域或用户ID..." class="search-input" />
        <div class="filter-group">
          <button class="filter-btn active">全部用户</button>
          <button class="filter-btn">高能耗</button>
          <button class="filter-btn">低能耗</button>
        </div>
      </div>
      <div class="map-container card">
        <div class="leaflet-placeholder">
          <span>Leaflet 地图加载区域</span>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import MainLayout from '@/components/MainLayout.vue'
</script>

<style scoped>
.map-page-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.map-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: white;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.search-input {
  width: 300px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 6px 16px;
  border: 1px solid var(--border-color);
  background: white;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  color: var(--text-regular);
}

.filter-btn.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.map-container {
  flex: 1;
  min-height: 0;
  padding: 0; /* 地图通常不需要内边距 */
  overflow: hidden;
  position: relative;
}

.leaflet-placeholder {
  width: 100%;
  height: 100%;
  background: #eef2f6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
}
</style>
