/**
 * 地图相关API
 */
import request from '@/utils/request'

/**
 * 获取用户坐标点集
 * @param {number} limit - 限制返回数量
 */
export function getMapPoints(limit = 1000) {
    return request({
        url: '/map/points',
        method: 'get',
        params: { limit }
    })
}
