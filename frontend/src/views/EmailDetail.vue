<template>
  <div class="email-detail">
    <el-page-header @back="goBack" title="邮件详情" />
    
    <div v-if="loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>
    
    <template v-else-if="email">
      <el-row :gutter="20" class="detail-content">
        <!-- 左侧：邮件信息 -->
        <el-col :span="14">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>📧 邮件信息</span>
                <el-tag :type="getStatusType(email.status)">
                  {{ getStatusText(email.status) }}
                </el-tag>
              </div>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="发件人" :span="2">
                {{ email.sender }}
              </el-descriptions-item>
              <el-descriptions-item label="主题" :span="2">
                {{ email.subject }}
              </el-descriptions-item>
              <el-descriptions-item label="平台">
                {{ email.platform || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="应用版本">
                {{ email.app_version || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="设备" :span="2">
                {{ email.device || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="账号ID">
                {{ email.account_id || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="玩家名">
                {{ email.player_name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="接收时间" :span="2">
                {{ formatDate(email.received_at) }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="email-content">
              <h4>邮件内容：</h4>
              <pre>{{ email.content }}</pre>
            </div>
          </el-card>
          
          <!-- 回复列表 -->
          <el-card v-if="email.replies?.length" class="replies-card">
            <template #header>
              <div class="card-header">
                <span>💬 回复记录</span>
              </div>
            </template>
            
            <el-timeline>
              <el-timeline-item
                v-for="reply in email.replies"
                :key="reply.id"
                :type="reply.is_sent ? 'success' : 'warning'"
                :timestamp="formatDate(reply.created_at)"
              >
                <el-card>
                  <p><strong>生成方式：</strong>{{ reply.generated_by }}</p>
                  <p><strong>内容：</strong></p>
                  <pre>{{ reply.content }}</pre>
                  <el-tag v-if="reply.is_sent" type="success" size="small">已发送</el-tag>
                  <el-tag v-else type="warning" size="small">未发送</el-tag>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
        
        <!-- 右侧：分析和操作 -->
        <el-col :span="10">
          <!-- 分析结果 -->
          <el-card v-if="email.analysis">
            <template #header>
              <div class="card-header">
                <span>🎯 智能分析</span>
                <el-button link type="primary" @click="reanalyze">重新分析</el-button>
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="问题类型">
                <el-tag :type="getQuestionTypeType(email.analysis.question_type)">
                  {{ email.analysis.question_type }}
                </el-tag>
                <span class="confidence">
                  (置信度: {{ (email.analysis.question_type_confidence * 100).toFixed(0) }}%)
                </span>
              </el-descriptions-item>
              
              <el-descriptions-item label="紧急度">
                <el-tag :type="getUrgencyType(email.analysis.urgency)">
                  {{ getUrgencyText(email.analysis.urgency) }}
                </el-tag>
                <span class="confidence">
                  (置信度: {{ (email.analysis.urgency_confidence * 100).toFixed(0) }}%)
                </span>
              </el-descriptions-item>
              
              <el-descriptions-item label="情绪">
                {{ email.analysis.sentiment }}
                <span class="confidence">
                  (置信度: {{ (email.analysis.sentiment_confidence * 100).toFixed(0) }}%)
                </span>
              </el-descriptions-item>
              
              <el-descriptions-item label="紧急原因">
                {{ email.analysis.urgency_reason || '-' }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="suggestions" v-if="email.analysis.suggestions && email.analysis.suggestions.length > 0">
              <h4>💡 处理建议：</h4>
              <ul>
                <li v-for="(suggestion, index) in email.analysis.suggestions" :key="index">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
            <div class="suggestions" v-else>
              <h4>💡 处理建议：</h4>
              <p style="color: #909399;">暂无处理建议</p>
            </div>
          </el-card>
          
          <el-card v-else>
            <el-empty description="暂无分析结果">
              <el-button type="primary" @click="analyze">进行分析</el-button>
            </el-empty>
          </el-card>
          
          <!-- 生成回复 -->
          <el-card class="reply-card">
            <template #header>
              <div class="card-header">
                <span>✍️ 生成回复</span>
              </div>
            </template>
            
            <el-form>
              <el-form-item>
                <el-checkbox v-model="useLLM">使用LLM生成</el-checkbox>
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="generating"
                  @click="generateReply"
                  style="width: 100%"
                >
                  生成回复
                </el-button>
              </el-form-item>
            </el-form>
            
            <template v-if="generatedReply">
              <el-divider />
              
              <el-input
                v-model="generatedReply.content"
                type="textarea"
                :rows="8"
              />
              
              <div class="reply-actions">
                <el-button type="success" @click="sendReply">
                  <el-icon><Promotion /></el-icon>
                  发送回复
                </el-button>
                <el-button @click="copyReply">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </template>
    
    <el-empty v-else description="邮件不存在" />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { emailApi } from '../api'

export default {
  name: 'EmailDetail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const emailId = route.params.id
    
    const loading = ref(false)
    const email = ref(null)
    const useLLM = ref(true)
    const generating = ref(false)
    const generatedReply = ref(null)
    
    // 加载邮件详情
    const loadEmail = async () => {
      loading.value = true
      try {
        const res = await emailApi.getDetail(emailId)
        if (res.success) {
          email.value = res.email
          // 确保 suggestions 是数组
          if (email.value?.analysis?.suggestions) {
            const suggestions = email.value.analysis.suggestions
            if (typeof suggestions === 'string') {
              try {
                email.value.analysis.suggestions = JSON.parse(suggestions)
              } catch (e) {
                email.value.analysis.suggestions = []
              }
            }
          }
        } else {
          ElMessage.error('邮件不存在')
        }
      } catch (error) {
        ElMessage.error(error.message || '加载失败')
      } finally {
        loading.value = false
      }
    }
    
    // 分析邮件
    const analyze = async () => {
      try {
        const res = await emailApi.analyze(emailId)
        if (res.success) {
          email.value.analysis = res.analysis
          ElMessage.success('分析完成')
        }
      } catch (error) {
        ElMessage.error(error.message || '分析失败')
      }
    }
    
    // 重新分析
    const reanalyze = () => {
      analyze()
    }
    
    // 生成回复
    const generateReply = async () => {
      generating.value = true
      try {
        const res = await emailApi.generateReply(emailId, { use_llm: useLLM.value })
        if (res.success) {
          generatedReply.value = res.reply
          ElMessage.success('回复生成成功')
        }
      } catch (error) {
        ElMessage.error(error.message || '生成失败')
      } finally {
        generating.value = false
      }
    }
    
    // 发送回复
    const sendReply = async () => {
      if (!generatedReply.value) return
      
      try {
        const res = await emailApi.sendReply(emailId, {
          content: generatedReply.value.content
        })
        
        if (res.success) {
          ElMessage.success('回复已发送')
          loadEmail() // 刷新
        }
      } catch (error) {
        ElMessage.error(error.message || '发送失败')
      }
    }
    
    // 复制回复
    const copyReply = () => {
      if (!generatedReply.value?.content) return
      
      navigator.clipboard.writeText(generatedReply.value.content)
        .then(() => ElMessage.success('已复制到剪贴板'))
        .catch(() => ElMessage.error('复制失败'))
    }
    
    // 返回
    const goBack = () => {
      console.log('goBack called')
      // 清理状态
      email.value = null
      generatedReply.value = null
      router.push('/emails')
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
      console.log('EmailDetail mounted, emailId:', emailId)
      loadEmail()
    })
    
    onUnmounted(() => {
      console.log('EmailDetail unmounted')
      // 清理状态
      email.value = null
      generatedReply.value = null
    })
    
    return {
      loading,
      email,
      useLLM,
      generating,
      generatedReply,
      loadEmail,
      analyze,
      reanalyze,
      generateReply,
      sendReply,
      copyReply,
      goBack,
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
.email-detail {
  padding: 20px;
}

.loading {
  padding: 40px;
}

.detail-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.email-content {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.email-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  margin-top: 10px;
}

.confidence {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.suggestions {
  margin-top: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.suggestions h4 {
  margin-bottom: 10px;
}

.suggestions ul {
  padding-left: 20px;
}

.replies-card {
  margin-top: 20px;
}

.reply-card {
  margin-top: 20px;
}

.reply-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}
</style>
