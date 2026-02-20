<template>
  <div class="layout-wrapper">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-icon"></span>
        <span class="logo-text">用电分析平台</span>
      </div>
      <nav class="menu">
        <router-link to="/dashboard" class="menu-item" active-class="active">
          <span class="icon"></span>
          <span class="text">仪表盘</span>
        </router-link>
        <router-link to="/query" class="menu-item" active-class="active">
          <span class="icon"></span>
          <span class="text">用户查询</span>
        </router-link>
        <router-link to="/cluster" class="menu-item" active-class="active">
          <span class="icon"></span>
          <span class="text">用户聚类</span>
        </router-link>
        <router-link to="/industry" class="menu-item" active-class="active">
          <span class="icon"></span>
          <span class="text">行业分析</span>
        </router-link>
        <router-link to="/predict" class="menu-item" active-class="active">
          <span class="icon"></span>
          <span class="text">行业预测</span>
        </router-link>
        <router-link to="/map" class="menu-item" active-class="active">
          <span class="icon"></span>
          <span class="text">电力地图</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主体内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="header">
        <div class="header-left">
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>
        <div class="header-right">
          <div class="user-profile">
            <span class="avatar">A</span>
            <span class="username">Admin</span>
            <button class="logout-link" @click="handleLogout">退出</button>
          </div>
        </div>
      </header>

      <!-- 内容显示区 -->
      <div class="page-container">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const pageTitles = {
  'Dashboard': '综合仪表盘',
  'Query': '用户数据查询',
  'Cluster': '用户用电行为聚类',
  'IndustryAnalysis': '行业用电分析',
  'Predict': '行业用电趋势预测',
  'Map': '区域电力分布'
}

const currentPageTitle = computed(() => {
  return pageTitles[route.name] || '用电分析平台'
})

const handleLogout = () => {
  if(confirm('确定要退出登录吗？')) {
    localStorage.removeItem('token')
    router.push('/login')
  } 
}
</script>

<style scoped>
.layout-wrapper {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-body);
}

/* 侧边栏样式 */
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 20px;
}

.logo-icon {
  margin-right: 8px;
  font-size: 24px;
  color: var(--primary-color); 
  /* 这里的primary-color可能需要在深色背景下调整，或者直接用亮一点的蓝色 */
  color: #4facfe;
}

.menu {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
  border-left: 3px solid transparent;
  margin-bottom: 4px;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.menu-item.active {
  background: linear-gradient(90deg, rgba(22, 93, 255, 0.2) 0%, rgba(22, 93, 255, 0) 100%);
  color: #fff;
  border-left-color: #165DFF; /* 使用稍亮一点的主色 */
  font-weight: 500;
}

.menu-item .icon {
  margin-right: 12px;
  font-size: 18px;
  width: 24px;
  text-align: center;
}

/* 主体区域样式 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 防止内容溢出 */
  background: var(--bg-body);
}

.header {
  height: var(--header-height);
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  z-index: 90;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 32px;
  height: 32px;
  background: var(--primary-color);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.username {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.logout-link {
  margin-left: 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.logout-link:hover {
  background: #f2f3f5;
  color: var(--danger-color);
}

/* 页面容器 */
.page-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
</style>
