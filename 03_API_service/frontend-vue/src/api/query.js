/**
 * 用户查询相关API
 */
import request from '@/utils/request'

/**
 * 获取用户列表（分页）
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.keyword - 搜索关键词（可选）
 * @returns {Promise}
 */
export function getUserList(params) {
    return request({
        url: '/query/users',
        method: 'get',
        params
    })
}

/**
 * 上传CSV文件导入用户数据
 * @param {File} file - CSV文件对象
 * @returns {Promise}
 */
export function uploadCSV(file) {
    const formData = new FormData()
    formData.append('file', file)

    return request({
        url: '/query/upload-csv',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}
