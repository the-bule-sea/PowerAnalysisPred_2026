<template>
  <div class="map-page">
    <nav class="navbar">
      <h1 class="logo">用电分析平台</h1>
      <div class="nav-links">
        <router-link to="/dashboard" class="nav-link">首页</router-link>
        <router-link to="/cluster" class="nav-link">用户聚类</router-link>
        <router-link to="/predict" class="nav-link">行业预测</router-link>
        <router-link to="/map" class="nav-link">电力地图</router-link>
        <button @click="handleLogout" class="logout-btn">退出</button>
      </div>
    </nav>
    <div class="content">
      <h2>电力地图可视化</h2>
      <div class="placeholder">
        <p>此页面将展示用户地理分布</p>
        <p>TODO: 集成Leaflet地图和用户坐标点</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
// TODO: 引入 getMapPoints

const router = useRouter()

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

// TODO: 加载地图数据并渲染Leaflet地图
</script>

<style scoped>
.map-page {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.logo {
  font-size: 24px;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 5px;
  transition: background 0.3s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.2);
}

.logout-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid white;
  color: white;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.content {
  flex: 1;
  padding: 40px;
  background: #f5f5f5;
}

.content h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.placeholder {
  background: white;
  padding: 40px;
  border-radius: 10px;
  text-align: center;
}

.placeholder p {
  color: #666;
  margin: 10px 0;
  font-size: 16px;
}
</style>
