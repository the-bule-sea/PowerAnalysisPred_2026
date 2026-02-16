<template>
  <div class="login-container">
    <div class="glass-bg"></div>
    <div class="login-wrapper">
      <div class="login-card">
        <div class="title-wrapper">
          <h1 class="platform-title">💡 电力数据分析与预测平台</h1>
          <p class="subtitle">让数据驱动能源未来</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label class="input-label">账号</label>
            <div class="input-wrapper">
              <span class="prefix-icon">👤</span>
              <input 
                v-model="loginForm.username" 
                type="text" 
                placeholder="请输入管理员账号"
                required
              />
            </div>
          </div>
          
          <div class="form-group">
            <label class="input-label">密码</label>
            <div class="input-wrapper">
              <span class="prefix-icon">🔒</span>
              <input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="请输入登录密码"
                required
              />
            </div>
          </div>
          
          <button type="submit" class="login-btn" :disabled="loading">
            <span v-if="loading">登录中...</span>
            <span v-else>立即登录</span>
          </button>
          
          <p v-if="error" class="error-msg">{{ error }}</p>
          
          <div class="footer-links">
            <a href="#" class="forgot-link">忘记密码?</a>
            <span class="divider">|</span>
            <a href="#" class="register-link">申请试用</a>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'

const router = useRouter()

const loginForm = ref({
  username: 'admin',
  password: '123456'
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // 这里使用模拟登录进行调试，如果需要真实接口请放开下面注释
    // const res = await login(loginForm.value)
    // localStorage.setItem('token', res.data.token)
    
    // 模拟成功
    localStorage.setItem('token', 'mock-token')
    await new Promise(r => setTimeout(r, 800))
    
    router.push('/dashboard')
  } catch (err) {
    error.value = err.message || '登录失败，请检查网络或账号'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background: linear-gradient(135deg, #1A237E 0%, #0D47A1 100%);
}

/* 背景装饰 */
.glass-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 120%;
  background-image: 
    radial-gradient(circle at 20% 30%, rgba(68, 138, 255, 0.4) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(0, 229, 255, 0.3) 0%, transparent 40%);
  z-index: 0;
  pointer-events: none;
}

.login-wrapper {
  position: relative;
  z-index: 10;
  perspective: 1000px;
}

.login-card {
  width: 440px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 48px;
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1);
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px) rotateX(5deg); }
  to { opacity: 1; transform: translateY(0) rotateX(0); }
}

.title-wrapper {
  text-align: center;
  margin-bottom: 40px;
}

.platform-title {
  font-size: 24px;
  font-weight: 700;
  color: #1A237E;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.subtitle {
  color: #5C6BC0;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-label {
  font-size: 14px;
  color: #3949AB;
  font-weight: 600;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.prefix-icon {
  position: absolute;
  left: 14px;
  color: #9FA8DA;
  font-size: 16px;
  z-index: 1;
}

.input-wrapper input {
  width: 100%;
  padding: 12px 14px 12px 42px;
  border: 1px solid #E8EAF6;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s;
  background: #FAFAFA;
}

.input-wrapper input:focus {
  border-color: #3D5AFE;
  box-shadow: 0 0 0 3px rgba(61, 90, 254, 0.15);
  background: #FFF;
}

.login-btn {
  background: linear-gradient(90deg, #304FFE 0%, #3D5AFE 100%);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 8px;
  box-shadow: 0 4px 12px rgba(48, 79, 254, 0.3);
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(48, 79, 254, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-msg {
  color: #FF1744;
  text-align: center;
  font-size: 13px;
  background: rgba(255, 23, 68, 0.1);
  padding: 8px;
  border-radius: 4px;
}

.footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #9E9E9E;
  margin-top: 16px;
}

.footer-links a {
  color: #7986CB;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-links a:hover {
  color: #304FFE;
}

.divider {
  color: #E0E0E0;
}
</style>
