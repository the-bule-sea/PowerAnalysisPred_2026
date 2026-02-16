<template>
  <MainLayout>
    <div class="query-page">
      <!-- 操作栏 -->
      <div class="action-bar card">
        <div class="left">
          <input 
            type="file" 
            ref="fileInput" 
            accept=".csv"
            style="display: none"
            @change="handleFileSelect"
          />
          <button class="btn btn-primary" @click="triggerFileInput" :disabled="uploading">
            {{ uploading ? '上传中...' : '导入CSV数据' }}
          </button>
          <button class="btn btn-secondary">导出数据</button>
        </div>
        <div class="right">
          <input 
            type="text" 
            placeholder="搜索用采ID或电表ID..." 
            class="search-input"
            v-model="searchKeyword"
            @keyup.enter="handleSearch"
          />
          <button class="btn btn-secondary" @click="handleSearch">搜索</button>
        </div>
      </div>

      <!-- 数据表格 -->
      <div class="table-container card">
        <table class="data-table">
          <thead>
            <tr>
              <th>NO</th>
              <th>用采ID</th>
              <th>电表ID</th>
              <th>立户时间</th>
              <th>行业分类</th>
              <th>用电类型</th>
              <th>用户分类</th>
              <th>供电电压</th>
              <th>合同容量</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody v-if="!loading && tableData.length > 0">
            <tr v-for="row in tableData" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.yc_id }}</td>
              <td>{{ row.meter_id }}</td>
              <td>{{ row.build_date }}</td>
              <td>{{ row.trade_code }}</td>
              <td>{{ row.elec_type_code }}</td>
              <td>{{ row.cons_sort_code }}</td>
              <td>{{ row.volt_code }}</td>
              <td>{{ row.contract_cap }}</td>
              <td>
                <button class="action-btn">查看</button>
              </td>
            </tr>
          </tbody>
          <tbody v-else-if="loading">
            <tr>
              <td colspan="10" class="loading-cell">加载中...</td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="10" class="empty-cell">暂无数据</td>
            </tr>
          </tbody>
        </table>

        <!-- 分页 -->
        <div class="pagination">
          <div class="pagination-info">
            Showing {{ (currentPage - 1) * pageSize + 1 }} to {{ Math.min(currentPage * pageSize, total) }} of {{ total }} rows
          </div>
          <div class="pagination-controls">
            <input 
              type="number" 
              v-model.number="pageSize" 
              @change="handlePageSizeChange"
              class="page-size-input"
              min="10"
              max="100"
            />
            <span class="label">rows per page</span>
            
            <div class="page-numbers">
              <button 
                class="page-btn"
                :disabled="currentPage === 1"
                @click="goToPage(currentPage - 1)"
              >
                &lt;
              </button>
              
              <button 
                v-for="page in visiblePages" 
                :key="page"
                :class="['page-btn', { active: page === currentPage }]"
                @click="goToPage(page)"
              >
                {{ page }}
              </button>
              
              <button 
                class="page-btn"
                :disabled="currentPage === totalPages"
                @click="goToPage(currentPage + 1)"
              >
                &gt;
              </button>
              
              <button 
                class="page-btn"
                @click="goToPage(totalPages)"
                :disabled="currentPage === totalPages"
              >
                {{ totalPages }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { getUserList, uploadCSV } from '@/api/query'

const tableData = ref([])
const loading = ref(false)
const uploading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchKeyword = ref('')
const fileInput = ref(null)

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value)
})

// 计算可见的页码
const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - 2)
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i < end; i++) {
    pages.push(i)
  }
  
  return pages
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined
    })
    
    tableData.value = res.data.list
    total.value = res.data.total
  } catch (error) {
    console.error('加载数据失败:', error)
    alert('加载数据失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value.click()
}

// 处理文件选择
const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件类型
  if (!file.name.endsWith('.csv')) {
    alert('请选择CSV格式文件')
    return
  }
  
  if (confirm(`确定要导入 "${file.name}" 吗？数据将被插入到数据库中。`)) {
    await handleUpload(file)
  }
  
  // 重置输入框
  event.target.value = ''
}

// 处理上传
const handleUpload = async (file) => {
  uploading.value = true
  try {
    const res = await uploadCSV(file)
    
    const result = res.data
    let message = `导入完成！\n总计: ${result.total} 条\n成功: ${result.success_count} 条\n失败: ${result.error_count} 条`
    
    if (result.errors && result.errors.length > 0) {
      message += `\n\n错误详情（前10条）:\n${result.errors.join('\n')}`
    }
    
    alert(message)
    
    // 导入成功后刷新数据
    if (result.success_count > 0) {
      currentPage.value = 1
      await loadData()
    }
  } catch (error) {
    console.error('上传失败:', error)
    alert(`导入失败: ${error.response?.data?.msg || error.message}`)
  } finally {
    uploading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

// 跳转到指定页
const goToPage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadData()
}

// 每页数量变化
const handlePageSizeChange = () => {
  currentPage.value = 1
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.query-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.action-bar {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-bar .left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-bar .right {
  display: flex;
  gap: 8px;
}

.search-input {
  width: 280px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table thead {
  background: #f7f8fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

.data-table tbody {
  overflow-y: auto;
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-regular);
}

.data-table tbody tr:hover {
  background: #f9fafb;
}

.action-btn {
  color: var(--primary-color);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
}

.action-btn:hover {
  text-decoration: underline;
}

.loading-cell,
.empty-cell {
  text-align: center;
  color: var(--text-placeholder);
  padding: 40px !important;
}

/* 分页 */
.pagination {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
  background: #fafbfc;
}

.pagination-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-size-input {
  width: 60px;
  padding: 6px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  text-align: center;
}

.label {
  font-size: 13px;
  color: var(--text-secondary);
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid var(--border-color);
  background: white;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-regular);
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.page-btn.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.page-btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}
</style>

