<template>
  <div class="emails">
    <h2 class="page-title">📧 邮件管理</h2>
    
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable>
            <el-option label="新邮件" value="new" />
            <el-option label="待审核" value="pending_review" />
            <el-option label="已回复" value="replied" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="问题类型">
          <el-select v-model="filterForm.question_type" placeholder="全部类型" clearable>
            <el-option label="充值问题" value="充值问题" />
            <el-option label="BUG反馈" value="BUG反馈" />
            <el-option label="意见建议" value="意见建议" />
            <el-option label="账号问题" value="账号问题" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="紧急度">
          <el-select v-model="filterForm.urgency" placeholder="全部" clearable>
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadEmails">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 邮件列表 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="emails"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column type="index" width="50" />
        
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="sender" label="发件人" width="200" show-overflow-tooltip />
        
        <el-table-column prop="subject" label="主题" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="question_type" label="问题类型" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.question_type" :type="getQuestionTypeType(row.question_type)">
              {{ row.question_type }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="urgency" label="紧急度" width="100">
          <template #default="{ row }">
            <el-tag :type="getUrgencyType(row.urgency)" size="small">
              {{ getUrgencyText(row.urgency) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="received_at" label="接收时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.received_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="viewEmail(row.id)">查看</el-button>
            <el-button 
              v-if="row.status !== 'replied'" 
              link 
              type="success" 
              @click.stop="quickReply(row.id)"
            >
              回复
            </el-button>
            <el-button 
              link 
              type="danger" 
              @click.stop="deleteEmail(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { emailApi } from '../api'

export default {
  name: 'Emails',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const emails = ref([])
    
    const filterForm = reactive({
      status: '',
      question_type: '',
      urgency: ''
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    
    // 加载邮件列表
    const loadEmails = async () => {
      loading.value = true
      try {
        const res = await emailApi.getList({
          status: filterForm.status || undefined,
          page: pagination.page,
          per_page: pagination.per_page
        })
        
        if (res.success) {
          emails.value = res.emails || []
          pagination.total = res.total || emails.value.length
        }
      } catch (error) {
        ElMessage.error(error.message || '加载失败')
      } finally {
        loading.value = false
      }
    }
    
    // 重置筛选
    const resetFilter = () => {
      filterForm.status = ''
      filterForm.question_type = ''
      filterForm.urgency = ''
      loadEmails()
    }
    
    // 查看邮件详情
    const viewEmail = (id) => {
      router.push(`/email/${id}`)
    }
    
    // 快速回复
    const quickReply = (id) => {
      router.push(`/email/${id}`)
    }
    
    // 删除邮件
    const deleteEmail = async (id) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这封邮件吗？删除后无法恢复。',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        const res = await emailApi.delete(id)
        if (res.success) {
          ElMessage.success('邮件已删除')
          loadEmails() // 刷新列表
        } else {
          ElMessage.error(res.message || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(error.message || '删除失败')
        }
      }
    }
    
    // 行点击
    const handleRowClick = (row) => {
      viewEmail(row.id)
    }
    
    // 分页处理
    const handleSizeChange = (size) => {
      pagination.per_page = size
      loadEmails()
    }
    
    const handlePageChange = (page) => {
      pagination.page = page
      loadEmails()
    }
    
    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }
    
    // 获取标签类型
    const getQuestionTypeType = (type) => {
      const types = {
        '充值问题': 'danger',
        'BUG反馈': 'warning',
        '意见建议': 'success',
        '账号问题': 'info'
      }
      return types[type] || ''
    }
    
    const getUrgencyType = (urgency) => {
      const types = { high: 'danger', medium: 'warning', low: 'success' }
      return types[urgency] || 'info'
    }
    
    const getUrgencyText = (urgency) => {
      const texts = { high: '高', medium: '中', low: '低' }
      return texts[urgency] || urgency
    }
    
    const getStatusType = (status) => {
      const types = { new: 'info', pending_review: 'warning', replied: 'success' }
      return types[status] || 'info'
    }
    
    const getStatusText = (status) => {
      const texts = { new: '新邮件', pending_review: '待审核', replied: '已回复' }
      return texts[status] || status
    }
    
    onMounted(() => {
      loadEmails()
    })
    
    return {
      loading,
      emails,
      filterForm,
      pagination,
      loadEmails,
      resetFilter,
      viewEmail,
      quickReply,
      deleteEmail,
      handleRowClick,
      handleSizeChange,
      handlePageChange,
      formatDate,
      getQuestionTypeType,
      getUrgencyType,
      getUrgencyText,
      getStatusType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.el-table__row {
  cursor: pointer;
}

.el-table__row:hover {
  background-color: #f5f7fa;
}
</style>
