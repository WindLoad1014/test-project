<template>
  <div class="auto-reply">
    <h2 class="page-title">🤖 自动回复</h2>
    
    <el-row :gutter="20">
      <!-- 左侧：邮件输入 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📧 邮件内容</span>
            </div>
          </template>
          
          <el-form :model="emailForm" label-position="top">
            <el-form-item label="发件人">
              <el-input v-model="emailForm.sender" placeholder="player@example.com" />
            </el-form-item>
            
            <el-form-item label="主题">
              <el-input v-model="emailForm.subject" placeholder="邮件主题" />
            </el-form-item>
            
            <el-form-item label="邮件内容">
              <el-input
                v-model="emailForm.content"
                type="textarea"
                :rows="12"
                placeholder="请将玩家邮件内容粘贴到此处..."
              />
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="emailForm.auto_send">满足条件时自动发送</el-checkbox>
              <el-tooltip content="仅当紧急度为低且置信度>80%时自动发送">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="emailForm.use_llm">使用LLM生成回复</el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="processing"
                @click="processEmail"
                style="width: 100%"
              >
                <el-icon><Promotion /></el-icon>
                {{ processing ? '处理中...' : '一键自动处理' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧：处理结果 -->
      <el-col :span="12">
        <el-card v-if="!result" class="empty-result">
          <el-empty description="请输入邮件内容并点击处理">
            <template #image>
              <el-icon size="80" color="#dcdfe6"><Message /></el-icon>
            </template>
          </el-empty>
        </el-card>
        
        <template v-else>
          <!-- 分析结果 -->
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>🎯 智能分析</span>
                <el-tag :type="getUrgencyType(result.analysis.urgency)">
                  {{ getUrgencyText(result.analysis.urgency) }}优先级
                </el-tag>
              </div>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="问题类型">
                {{ result.analysis.question_type }}
              </el-descriptions-item>
              <el-descriptions-item label="置信度">
                {{ (result.analysis.question_type_confidence * 100).toFixed(0) }}%
              </el-descriptions-item>
              <el-descriptions-item label="情绪" :span="2">
                {{ result.analysis.sentiment }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="suggestions" v-if="getSuggestions(result.analysis).length > 0">
              <h4>💡 处理建议：</h4>
              <ul>
                <li v-for="(suggestion, index) in getSuggestions(result.analysis)" :key="index">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
            <div class="suggestions" v-else>
              <h4>💡 处理建议：</h4>
              <p style="color: #909399;">暂无处理建议</p>
            </div>
          </el-card>
          
          <!-- 相似案例 -->
          <el-card class="result-card" v-if="result.analysis.similar_cases?.length">
            <template #header>
              <div class="card-header">
                <span>🔍 相似案例</span>
              </div>
            </template>
            
            <el-collapse>
              <el-collapse-item
                v-for="(caseItem, index) in result.analysis.similar_cases.slice(0, 3)"
                :key="index"
                :title="`案例 ${index + 1} (相似度: ${(caseItem.similarity * 100).toFixed(1)}%)`"
              >
                <p><strong>问题：</strong>{{ caseItem.question }}</p>
                <p><strong>回复：</strong>{{ caseItem.answer }}</p>
              </el-collapse-item>
            </el-collapse>
          </el-card>
          
          <!-- 生成的回复 -->
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>✍️ 生成的回复</span>
                <div>
                  <el-tag v-if="result.auto_sent" type="success" size="small">已自动发送</el-tag>
                  <el-tag v-else type="warning" size="small">待审核</el-tag>
                </div>
              </div>
            </template>
            
            <!-- 中日双语显示 -->
            <div class="bilingual-content">
              <div class="language-section">
                <div class="language-label">🇯🇵 日本語</div>
                <el-input
                  v-model="result.reply.content"
                  type="textarea"
                  :rows="6"
                  placeholder="日语回复内容"
                />
              </div>
              
              <div class="language-section" v-if="result.reply.content_zh">
                <div class="language-label">🇨🇳 中文对照</div>
                <el-input
                  v-model="result.reply.content_zh"
                  type="textarea"
                  :rows="6"
                  readonly
                  placeholder="中文翻译"
                />
              </div>
            </div>
            
            <div class="reply-actions">
              <el-button type="primary" @click="sendReply" v-if="!result.auto_sent">
                <el-icon><Promotion /></el-icon>
                发送回复
              </el-button>
              <el-button @click="regenerateReply">
                <el-icon><Refresh /></el-icon>
                重新生成
              </el-button>
              <el-button type="success" @click="copyReply">
                <el-icon><CopyDocument /></el-icon>
                复制日语
              </el-button>
              <el-button type="info" @click="copyChinese" v-if="result.reply.content_zh">
                <el-icon><CopyDocument /></el-icon>
                复制中文
              </el-button>
            </div>
          </el-card>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { emailApi } from '../api'

export default {
  name: 'AutoReply',
  setup() {
    const processing = ref(false)
    const result = ref(null)
    
    const emailForm = reactive({
      sender: '',
      subject: '',
      content: '',
      auto_send: false,
      use_llm: true
    })
    
    // 处理邮件
    const processEmail = async () => {
      if (!emailForm.content.trim()) {
        ElMessage.warning('请输入邮件内容')
        return
      }
      
      processing.value = true
      try {
        const res = await emailApi.autoProcess({
          sender: emailForm.sender || 'unknown@example.com',
          subject: emailForm.subject || '无主题',
          content: emailForm.content,
          auto_send: emailForm.auto_send,
          use_llm: emailForm.use_llm
        })
        
        if (res.success) {
          // 确保 analysis 和 suggestions 格式正确
          if (res.analysis) {
            // 如果 suggestions 是字符串，尝试解析为数组
            if (typeof res.analysis.suggestions === 'string') {
              try {
                res.analysis.suggestions = JSON.parse(res.analysis.suggestions)
              } catch (e) {
                console.warn('suggestions is not valid JSON:', res.analysis.suggestions)
                res.analysis.suggestions = []
              }
            }
            // 确保 suggestions 是数组
            if (!Array.isArray(res.analysis.suggestions)) {
              console.warn('suggestions is not an array:', res.analysis.suggestions)
              res.analysis.suggestions = []
            }
          }
          result.value = res
          console.log('处理结果:', result.value)
          ElMessage.success(res.message)
        } else {
          ElMessage.error(res.message || '处理失败')
        }
      } catch (error) {
        console.error('处理邮件错误:', error)
        if (error.code === 'ECONNABORTED') {
          ElMessage.error('请求超时，LLM生成可能需要更长时间，请稍后重试')
        } else if (error.message && error.message.includes('Network Error')) {
          ElMessage.error('网络错误，请检查后端服务是否正常运行')
        } else {
          ElMessage.error(error.message || '处理失败')
        }
      } finally {
        processing.value = false
      }
    }
    
    // 发送回复
    const sendReply = async () => {
      if (!result.value) return
      
      try {
        const res = await emailApi.sendReply(result.value.email_id, {
          content: result.value.reply.content
        })
        
        if (res.success) {
          result.value.auto_sent = true
          ElMessage.success('回复已发送')
        }
      } catch (error) {
        ElMessage.error(error.message || '发送失败')
      }
    }
    
    // 重新生成
    const regenerateReply = async () => {
      if (!result.value) return
      
      processing.value = true
      try {
        const res = await emailApi.generateReply(result.value.email_id, {
          use_llm: emailForm.use_llm
        })
        
        if (res.success) {
          result.value.reply = res.reply
          ElMessage.success('回复已重新生成')
        }
      } catch (error) {
        console.error('重新生成错误:', error)
        if (error.code === 'ECONNABORTED') {
          ElMessage.error('请求超时，LLM生成可能需要更长时间，请稍后重试')
        } else {
          ElMessage.error(error.message || '生成失败')
        }
      } finally {
        processing.value = false
      }
    }
    
    // 复制日语回复
    const copyReply = () => {
      if (!result.value?.reply?.content) return
      
      navigator.clipboard.writeText(result.value.reply.content)
        .then(() => ElMessage.success('日语内容已复制到剪贴板'))
        .catch(() => ElMessage.error('复制失败'))
    }
    
    // 复制中文回复
    const copyChinese = () => {
      if (!result.value?.reply?.content_zh) return
      
      navigator.clipboard.writeText(result.value.reply.content_zh)
        .then(() => ElMessage.success('中文内容已复制到剪贴板'))
        .catch(() => ElMessage.error('复制失败'))
    }
    
    // 工具函数
    const getUrgencyType = (urgency) => {
      const types = { high: 'danger', medium: 'warning', low: 'success' }
      return types[urgency] || 'info'
    }
    
    const getUrgencyText = (urgency) => {
      const texts = { high: '高', medium: '中', low: '低' }
      return texts[urgency] || urgency
    }
    
    // 确保 suggestions 是数组
    const getSuggestions = (analysis) => {
      if (!analysis || !analysis.suggestions) return []
      const suggestions = analysis.suggestions
      if (Array.isArray(suggestions)) return suggestions
      if (typeof suggestions === 'string') {
        try {
          const parsed = JSON.parse(suggestions)
          return Array.isArray(parsed) ? parsed : []
        } catch (e) {
          return []
        }
      }
      return []
    }
    
    return {
      emailForm,
      processing,
      result,
      processEmail,
      sendReply,
      regenerateReply,
      copyReply,
      getUrgencyType,
      getUrgencyText,
      getSuggestions,
      copyChinese
    }
  }
}
</script>

<style scoped>
.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.info-icon {
  margin-left: 5px;
  color: #909399;
  cursor: help;
}

.empty-result {
  height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-card {
  margin-bottom: 20px;
}

.suggestions {
  margin-top: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.suggestions h4 {
  margin-bottom: 10px;
  color: #303133;
}

.suggestions ul {
  padding-left: 20px;
}

.suggestions li {
  margin-bottom: 5px;
  color: #606266;
}

.reply-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.bilingual-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.language-section {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  background-color: #fafafa;
}

.language-label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
  font-size: 14px;
}
</style>
