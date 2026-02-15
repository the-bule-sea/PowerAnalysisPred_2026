/**
 * 认证相关API
 */
import request from '@/utils/request'

/**
 * 用户登录
 * @param {Object} data - 登录信息
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 */
export function login(data) {
    return request({
        url: '/auth/login',
        method: 'post',
        data
    })
}
