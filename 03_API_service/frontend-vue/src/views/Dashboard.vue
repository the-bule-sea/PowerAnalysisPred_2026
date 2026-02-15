<template>
  <div class="dashboard">
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
      <h2>欢迎使用用电行为分析与预测平台</h2>
      <div class="card-container">
        <div class="card" @click="$router.push('/cluster')">
          <h3>用户聚类分析</h3>
          <p>基于K-Means算法的用户用电行为分类</p>
        </div>
        <div class="card" @click="$router.push('/predict')">
          <h3>行业用电预测</h3>
          <p>使用LSTM和随机森林进行用电量预测</p>
        </div>
        <div class="card" @click="$router.push('/map')">
          <h3>电力地图可视化</h3>
          <p>基于地理信息的用户分布展示</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
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
  margin-bottom: 40px;
}

.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.card h3 {
  color: #667eea;
  margin-bottom: 15px;
  font-size: 20px;
}

.card p {
  color: #666;
  line-height: 1.6;
}
</style>
