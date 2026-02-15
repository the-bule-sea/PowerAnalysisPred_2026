/**
 * 聚类分析相关API
 */
import request from '@/utils/request'

/**
 * 获取聚类中心曲线
 */
export function getClusterCenters() {
    return request({
        url: '/cluster/centers',
        method: 'get'
    })
}

/**
 * 获取聚类统计分布
 */
export function getClusterStats() {
    return request({
        url: '/cluster/stats',
        method: 'get'
    })
}
