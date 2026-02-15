/**
 * Axios 实例配置
 * 统一处理API请求
 */
import axios from 'axios'
// 创建axios实例
const request = axios.create({
    baseURL: 'http://localhost:5000/api', // 后端API地址
    timeout: 10000, // 请求超时时间
    headers: {
        'Content-Type': 'application/json'
    }
})
// 请求拦截器
request.interceptors.request.use(
    config => {
        // 从localStorage获取token
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => {
        console.error('请求错误:', error)
        return Promise.reject(error)
    }
)
// 响应拦截器
request.interceptors.response.use(
    response => {
        const res = response.data

        // 根据业务状态码判断
        if (res.code === 200) {
            return res
        } else {
            // 业务错误
            console.error('业务错误:', res.msg)
            return Promise.reject(new Error(res.msg || '请求失败'))
        }
    },
    error => {
        console.error('响应错误:', error.message)

        // 处理HTTP错误
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    // 未授权，清除token并跳转登录
                    localStorage.removeItem('token')
                    window.location.href = '/login'
                    break
                case 403:
                    console.error('没有权限访问')
                    break
                case 404:
                    console.error('请求的资源不存在')
                    break
                case 500:
                    console.error('服务器错误')
                    break
                default:
                    console.error('未知错误')
            }
        }

        return Promise.reject(error)
    }
)
export default request