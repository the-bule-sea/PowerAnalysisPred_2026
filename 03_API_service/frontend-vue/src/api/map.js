/**
 * 地图相关API
 */
import request from '@/utils/request'

/**
 * 获取用户坐标点集
 * @param {Object} params - 查询参数
 * @param {number} params.limit - 限制返回数量
 * @param {number} [params.cluster_type] - 聚类类型筛选
 */
export function getMapPoints(params = { limit: 1000 }) {
    return request({
        url: '/map/points',
        method: 'get',
        params
    })
}
