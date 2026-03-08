<template>
  <div class="settings">
    <h2 class="page-title">⚙️ 系统设置</h2>
    
    <el-row :gutter="20">
      <!-- API配置 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔑 API配置</span>
            </div>
          </template>
          
          <el-form :model="apiForm" label-position="top">
            <el-form-item label="OpenAI API Key">
              <el-input
                v-model="apiForm.api_key"
                type="password"
                placeholder="sk-..."
                show-password
              />
            </el-form-item>
            
            <el-form-item label="API Base URL">
              <el-input v-model="apiForm.base_url" placeholder="https://api.openai.com/v1" />
            </el-form-item>
            
            <el-form-item label="模型">
              <el-select v-model="apiForm.model" style="width: 100%">
                <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
                <el-option label="GPT-4" value="gpt-4" />
                <el-option label="GPT-4 Turbo" value="gpt-4-turbo-preview" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveAPIConfig">保存配置</el-button>
              <el-button @click="testAPI">测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 数据库配置 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🗄️ 数据库配置</span>
            </div>
          </template>
          
          <el-form :model="dbForm" label-position="top">
            <el-form-item label="数据库类型">
              <el-radio-group v-model="dbForm.type">
                <el-radio label="sqlite">SQLite</el-radio>
                <el-radio label="mysql">MySQL</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <template v-if="dbForm.type === 'sqlite'">
              <el-form-item label="数据库文件路径">
                <el-input v-model="dbForm.sqlite_path" placeholder="data/cs_system.db" />
              </el-form-item>
            </template>
            
            <template v-if="dbForm.type === 'mysql'">
              <el-form-item label="主机">
                <el-input v-model="dbForm.mysql_host" placeholder="localhost" />
              </el-form-item>
              
              <el-form-item label="端口">
                <el-input-number v-model="dbForm.mysql_port" :min="1" :max="65535" />
              </el-form-item>
              
              <el-form-item label="用户名">
                <el-input v-model="dbForm.mysql_user" placeholder="root" />
              </el-form-item>
              
              <el-form-item label="密码">
                <el-input
                  v-model="dbForm.mysql_password"
                  type="password"
                  placeholder="密码"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="数据库名">
                <el-input v-model="dbForm.mysql_database" placeholder="cs_system" />
              </el-form-item>
            </template>
            
            <el-form-item>
              <el-button type="primary" @click="saveDBConfig">保存配置</el-button>
              <el-button @click="testDBConnection">测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 系统信息 -->
    <el-row :gutter="20" class="system-info">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>ℹ️ 系统信息</span>
            </div>
          </template>
          
          <el-descriptions :column="3" border>
            <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
            <el-descriptions-item label="后端框架">Flask</el-descriptions-item>
            <el-descriptions-item label="当前数据库">{{ dbForm.type.toUpperCase() }}</el-descriptions-item>
            <el-descriptions-item label="API状态">
              <el-tag :type="apiStatus.type">{{ apiStatus.text }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="最后更新">2026-03-06</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '../api'

export default {
  name: 'Settings',
  setup() {
    const apiStatus = reactive({
      type: 'info',
      text: '检查中...'
    })
    
    const apiForm = reactive({
      api_key: '',
      base_url: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo'
    })
    
    const dbForm = reactive({
      type: 'sqlite',
      sqlite_path: 'data/cs_system.db',
      mysql_host: 'localhost',
      mysql_port: 3306,
      mysql_user: 'root',
      mysql_password: '',
      mysql_database: 'cs_system'
    })
    
    // 检查API状态
    const checkAPIStatus = async () => {
      try {
        const res = await systemApi.health()
        if (res.status === 'ok') {
          apiStatus.type = 'success'
          apiStatus.text = '正常运行'
        } else {
          apiStatus.type = 'warning'
          apiStatus.text = '异常'
        }
      } catch (error) {
        apiStatus.type = 'danger'
        apiStatus.text = '无法连接'
      }
    }
    
    // 保存API配置
    const saveAPIConfig = () => {
      // 这里可以实现保存逻辑
      ElMessage.success('API配置已保存')
    }
    
    // 测试API
    const testAPI = () => {
      if (!apiForm.api_key) {
        ElMessage.warning('请输入API Key')
        return
      }
      ElMessage.info('测试中...')
      // 实际测试逻辑
    }
    
    // 保存数据库配置
    const saveDBConfig = () => {
      ElMessage.success('数据库配置已保存')
    }
    
    // 测试数据库连接
    const testDBConnection = () => {
      ElMessage.info('测试中...')
      // 实际测试逻辑
    }
    
    onMounted(() => {
      checkAPIStatus()
    })
    
    return {
      apiStatus,
      apiForm,
      dbForm,
      saveAPIConfig,
      testAPI,
      saveDBConfig,
      testDBConnection
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
  font-weight: bold;
}

.system-info {
  margin-top: 20px;
}
</style>
