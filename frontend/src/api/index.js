import axios from 'axios'

// 创建axios实例
const api = axios.create({
    baseURL: 'http://localhost:5000/api',
    timeout: 120000,  // LLM生成可能需要较长时间，增加到120秒
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
api.interceptors.request.use(
    config => {
        // 添加token到请求头
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`)
        return config
    },
    error => {
        console.error('[API Request Error]', error)
        return Promise.reject(error)
    }
)

// 响应拦截器
api.interceptors.response.use(
    response => {
        console.log(`[API Response] ${response.config.url}`, response.data)
        // 确保返回的是对象，如果是字符串则尝试解析
        let data = response.data
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data)
            } catch (e) {
                console.warn('Response is not valid JSON:', data)
            }
        }
        return data
    },
    error => {
        console.error('[API Response Error]', error)
        
        // 处理401未授权错误
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        
        const message = error.response?.data?.error || '请求失败'
        return Promise.reject(new Error(message))
    }
)

// 认证相关API
export const authApi = {
    // 登录
    login: (data) => api.post('/auth/login', data),
    
    // 注册（需要管理员权限）
    register: (data) => api.post('/auth/register', data),
    
    // 获取当前用户信息
    getCurrentUser: () => api.get('/auth/me'),
    
    // 登出
    logout: () => api.post('/auth/logout')
}

// 邮件相关API
export const emailApi = {
    // 接收邮件
    receive: (data) => api.post('/email/receive', data),
    
    // 自动处理邮件（接收+分析+生成回复）
    autoProcess: (data) => api.post('/email/auto-process', data),
    
    // 分析邮件
    analyze: (emailId) => api.post(`/email/${emailId}/analyze`),
    
    // 生成回复
    generateReply: (emailId, data) => api.post(`/email/${emailId}/generate-reply`, data),
    
    // 发送回复
    sendReply: (emailId, data) => api.post(`/email/${emailId}/send-reply`, data),
    
    // 获取邮件列表
    getList: (params) => api.get('/emails', { params }),
    
    // 获取邮件详情
    getDetail: (emailId) => api.get(`/email/${emailId}`),
    
    // 删除邮件
    delete: (emailId) => api.delete(`/email/${emailId}`)
}

// 统计相关API
export const statsApi = {
    // 获取统计信息
    getStats: () => api.get('/stats')
}

// 知识库相关API
export const kbApi = {
    // 搜索知识库
    search: (data) => api.post('/knowledge-base/search', data)
}

// 系统相关API
export const systemApi = {
    // 健康检查
    health: () => api.get('/health')
}

export default api
