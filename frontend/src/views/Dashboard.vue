<template>
  <div class="dashboard">
    <h2 class="page-title">系统概览</h2>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6" v-for="stat in statistics" :key="stat.title">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-icon" :style="{ backgroundColor: stat.color }">
            <el-icon size="24" color="#fff">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-title">{{ stat.title }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快捷操作 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>⚡ 快捷操作</span>
            </div>
          </template>
          <div class="action-buttons">
            <el-button type="primary" size="large" @click="goToAutoReply">
              <el-icon><Promotion /></el-icon>
              自动处理邮件
            </el-button>
            <el-button type="success" size="large" @click="goToEmails">
              <el-icon><Message /></el-icon>
              查看邮件列表
            </el-button>
            <el-button type="warning" size="large" @click="goToKnowledgeBase">
              <el-icon><Collection /></el-icon>
              知识库管理
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📊 问题类型分布</span>
            </div>
          </template>
          <div class="chart-placeholder">
            <div v-for="(item, index) in questionTypes" :key="index" class="type-item">
              <span class="type-name">{{ item.name }}</span>
              <el-progress 
                :percentage="item.percentage" 
                :color="item.color"
                :stroke-width="16"
              />
              <span class="type-count">{{ item.count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近邮件 -->
    <el-card class="recent-emails">
      <template #header>
        <div class="card-header">
          <span>📧 最近邮件</span>
          <el-button text @click="goToEmails">查看全部</el-button>
        </div>
      </template>
      
      <el-table :data="recentEmails" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="sender" label="发件人" width="200" />
        <el-table-column prop="subject" label="主题" show-overflow-tooltip />
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
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewEmail(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { statsApi, emailApi } from '../api'

export default {
  name: 'Dashboard',
  setup() {
    const router = useRouter()
    const statistics = ref([
      { title: '总邮件数', value: 0, icon: 'Message', color: '#409EFF' },
      { title: '待处理', value: 0, icon: 'Warning', color: '#E6A23C' },
      { title: '已回复', value: 0, icon: 'CircleCheck', color: '#67C23A' },
      { title: '今日新增', value: 0, icon: 'TrendCharts', color: '#909399' }
    ])
    
    const questionTypes = ref([])
    const recentEmails = ref([])
    
    // 加载统计数据
    const loadStats = async () => {
      try {
        const res = await statsApi.getStats()
        if (res.success) {
          const stats = res.stats
          statistics.value[0].value = stats.total_emails || 0
          statistics.value[1].value = stats.new_emails + stats.pending_review || 0
          statistics.value[2].value = stats.replied_emails || 0
          statistics.value[3].value = stats.total_emails || 0
          
          // 问题类型分布
          const typeColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
          const total = Object.values(stats.question_types || {}).reduce((a, b) => a + b, 0)
          
          questionTypes.value = Object.entries(stats.question_types || {})
            .map(([name, count], index) => ({
              name,
              count,
              percentage: total > 0 ? Math.round((count / total) * 100) : 0,
              color: typeColors[index % typeColors.length]
            }))
            .sort((a, b) => b.count - a.count)
        }
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    }
    
    // 加载最近邮件
    const loadRecentEmails = async () => {
      try {
        const res = await emailApi.getList({ per_page: 5 })
        if (res.success) {
          recentEmails.value = res.emails || []
        }
      } catch (error) {
        console.error('加载邮件失败:', error)
      }
    }
    
    // 路由跳转
    const goToAutoReply = () => router.push('/auto-reply')
    const goToEmails = () => router.push('/emails')
    const goToKnowledgeBase = () => router.push('/knowledge-base')
    const viewEmail = (id) => router.push(`/email/${id}`)
    
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
      loadStats()
      loadRecentEmails()
    })
    
    return {
      statistics,
      questionTypes,
      recentEmails,
      goToAutoReply,
      goToEmails,
      goToKnowledgeBase,
      viewEmail,
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
.dashboard {
  padding-bottom: 20px;
}

.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.quick-actions {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.action-buttons .el-button {
  justify-content: flex-start;
  padding: 15px 20px;
}

.type-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.type-name {
  width: 100px;
  font-size: 14px;
}

.type-count {
  width: 50px;
  text-align: right;
  color: #909399;
}

.recent-emails {
  margin-top: 20px;
}
</style>
