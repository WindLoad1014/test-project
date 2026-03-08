<template>
  <div class="knowledge-base">
    <h2 class="page-title">📚 知识库</h2>
    
    <el-row :gutter="20">
      <!-- 左侧：搜索 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔍 搜索知识库</span>
            </div>
          </template>
          
          <el-form :model="searchForm" label-position="top">
            <el-form-item label="查询内容">
              <el-input
                v-model="searchForm.query"
                type="textarea"
                :rows="4"
                placeholder="输入玩家问题或关键词..."
              />
            </el-form-item>
            
            <el-form-item label="问题类型">
              <el-select v-model="searchForm.question_type" placeholder="全部类型" clearable style="width: 100%">
                <el-option label="充值问题" value="充值问题" />
                <el-option label="BUG反馈" value="BUG反馈" />
                <el-option label="意见建议" value="意见建议" />
                <el-option label="账号问题" value="账号问题" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="返回数量">
              <el-slider v-model="searchForm.top_k" :min="1" :max="10" show-stops />
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="searchForm.fuzzy">
                启用模糊搜索
                <el-tooltip content="模糊搜索可以找到关键词不完全匹配但语义相似的案例">
                  <el-icon class="info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="searching"
                @click="search"
                style="width: 100%"
              >
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 统计信息 -->
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>📊 知识库统计</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_qa_pairs }}</div>
                <div class="stat-label">问答对总数</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_keywords }}</div>
                <div class="stat-label">关键词总数</div>
              </div>
            </el-col>
          </el-row>
          
          <el-divider />
          
          <h4>问题类型分布</h4>
          <div v-for="(count, type) in stats.question_types" :key="type" class="type-item">
            <span>{{ type }}</span>
            <el-tag size="small">{{ count }}</el-tag>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：搜索结果 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📋 搜索结果</span>
              <span v-if="searchResults.length">共 {{ searchResults.length }} 条</span>
            </div>
          </template>
          
          <el-empty v-if="!searchResults.length" description="请输入查询内容并点击搜索" />
          
          <div v-else class="results-list">
            <el-card
              v-for="(result, index) in searchResults"
              :key="index"
              class="result-item"
              shadow="hover"
            >
              <div class="result-header">
                <el-tag :type="getQuestionTypeType(result.question_type_cn)" size="small">
                  {{ result.question_type_cn }}
                </el-tag>
                <el-tag type="info" size="small">
                  相似度: {{ (result.similarity * 100).toFixed(1) }}%
                </el-tag>
              </div>
              
              <div class="result-content">
                <h4>问题：</h4>
                <p>{{ result.question }}</p>
                
                <h4>回复：</h4>
                <pre>{{ result.answer }}</pre>
              </div>
              
              <div class="result-footer">
                <span>平台: {{ result.platform || '未知' }}</span>
                <el-button link type="primary" @click="useThisReply(result)">
                  使用此回复
                </el-button>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { kbApi } from '../api'

export default {
  name: 'KnowledgeBase',
  setup() {
    const searching = ref(false)
    const searchResults = ref([])
    
    const searchForm = reactive({
      query: '',
      question_type: '',
      top_k: 5,
      fuzzy: true  // 默认启用模糊搜索
    })
    
    const stats = reactive({
      total_qa_pairs: 2153,
      total_keywords: 172284,
      question_types: {
        'BUG反馈': 1278,
        '充值问题': 460,
        '意见建议': 352,
        '其他': 63
      }
    })
    
    // 搜索
    const search = async () => {
      if (!searchForm.query.trim()) {
        ElMessage.warning('请输入查询内容')
        return
      }
      
      searching.value = true
      try {
        const res = await kbApi.search({
          query: searchForm.query,
          top_k: searchForm.top_k,
          question_type: searchForm.question_type || undefined,
          fuzzy: searchForm.fuzzy
        })
        
        if (res.success) {
          searchResults.value = res.results || []
          if (searchResults.value.length === 0) {
            ElMessage.info('未找到相似案例')
          }
        }
      } catch (error) {
        ElMessage.error(error.message || '搜索失败')
      } finally {
        searching.value = false
      }
    }
    
    // 使用此回复
    const useThisReply = (result) => {
      navigator.clipboard.writeText(result.answer)
        .then(() => ElMessage.success('已复制到剪贴板'))
        .catch(() => ElMessage.error('复制失败'))
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
    
    return {
      searching,
      searchResults,
      searchForm,
      stats,
      search,
      useThisReply,
      getQuestionTypeType
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

.stats-card {
  margin-top: 20px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.type-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.type-item:last-child {
  border-bottom: none;
}

.info-icon {
  margin-left: 5px;
  color: #909399;
  cursor: help;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item {
  margin-bottom: 0;
}

.result-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.result-content h4 {
  margin: 10px 0 5px;
  color: #303133;
  font-size: 14px;
}

.result-content p {
  color: #606266;
  line-height: 1.6;
}

.result-content pre {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  color: #606266;
  line-height: 1.6;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
  color: #909399;
  font-size: 12px;
}
</style>
