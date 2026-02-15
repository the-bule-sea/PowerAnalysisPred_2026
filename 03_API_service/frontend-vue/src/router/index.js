/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import Cluster from '@/views/Cluster.vue'
import Predict from '@/views/Predict.vue'
import Map from '@/views/Map.vue'

const routes = [
    {
        path: '/',
        redirect: '/login'
    },
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
    },
    {
        path: '/cluster',
        name: 'Cluster',
        component: Cluster,
        meta: { requiresAuth: true }
    },
    {
        path: '/predict',
        name: 'Predict',
        component: Predict,
        meta: { requiresAuth: true }
    },
    {
        path: '/map',
        name: 'Map',
        component: Map,
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')

    if (to.meta.requiresAuth && !token) {
        // 需要认证但未登录，跳转到登录页
        next('/login')
    } else if (to.path === '/login' && token) {
        // 已登录用户访问登录页，跳转到首页
        next('/dashboard')
    } else {
        next()
    }
})

export default router
