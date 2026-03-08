/**
 * 行业分析与预测相关 API
 */
import request from '@/utils/request'

/**
 * 获取行业分类数据（饼图）
 */
export function getIndustryCategories() {
    return request({
        url: '/industry/categories',
        method: 'get'
    })
}

/**
 * 获取行业时序数据（折线图）
 * @param {number} level - 行业层级 1/2
 * @param {string} name - 行业名称
 */
export function getIndustryTimeseries(level, name) {
    return request({
        url: '/industry/timeseries',
        method: 'get',
        params: { level, name }
    })
}

/**
 * 上传 CSV 数据
 * @param {FormData} formData - 包含 file 字段的 FormData
 */
export function uploadIndustryCsv(formData) {
    return request({
        url: '/industry/upload-csv',
        method: 'post',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

/**
 * 清空行业用电数据
 */
export function clearIndustryData() {
    return request({
        url: '/industry/clear-data',
        method: 'delete'
    })
}

/**
 * 获取支持预测的行业列表
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
