/**
 * 行业预测相关API
 */
import request from '@/utils/request'

/**
 * 获取行业列表
 */
export function getIndustryList() {
    return request({
        url: '/industry/list',
        method: 'get'
    })
}

/**
 * 执行用电预测
 * @param {Object} data - 预测参数
 * @param {string} data.industry_id - 行业ID
 * @param {string} data.model_type - 模型类型 (lstm/rf)
 * @param {number} data.future_days - 预测天数
 */
export function predictIndustry(data) {
    return request({
        url: '/industry/predict',
        method: 'post',
        data
    })
}
