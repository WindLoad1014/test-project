<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28" color="#409EFF"><Service /></el-icon>
        <span class="logo-text">客服系统</span>
      </div>
      
      <el-menu
        :default-active="route.path"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item v-for="route in visibleRoutes" :key="route.path" :index="'/' + route.path">
          <el-icon>
            <component :is="route.meta.icon" />
          </el-icon>
          <span>{{ route.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ route.meta?.title || '客服系统' }}</span>
        </div>
        <div class="header-right">
          <el-badge :value="unreadCount" class="message-badge">
            <el-icon size="20"><Bell /></el-icon>
          </el-badge>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span>{{ currentUser?.username || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { statsApi, authApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'Layout',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const unreadCount = ref(0)
    
    // 获取当前用户信息
    const currentUser = computed(() => {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    })
    
    // 获取可见路由
    const visibleRoutes = computed(() => {
      return router.getRoutes()
        .find(r => r.path === '/')
        ?.children.filter(r => !r.meta?.hidden) || []
    })
    
    // 获取统计信息
    const loadStats = async () => {
      try {
        const res = await statsApi.getStats()
        if (res.success) {
          unreadCount.value = res.stats.new_emails || 0
        }
      } catch (error) {
        console.error('获取统计失败:', error)
      }
    }
    
    // 处理下拉菜单命令
    const handleCommand = async (command) => {
      if (command === 'logout') {
        try {
          await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          })
          
          // 调用登出API
          await authApi.logout()
          
          // 清除本地存储
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          
          ElMessage.success('已退出登录')
          
          // 跳转到登录页
          router.push('/login')
        } catch (error) {
          if (error !== 'cancel') {
            console.error('登出失败:', error)
            ElMessage.error('登出失败')
          }
        }
      } else if (command === 'profile') {
        ElMessage.info('个人设置功能开发中...')
      }
    }
    
    onMounted(() => {
      loadStats()
      // 每30秒刷新一次
      setInterval(loadStats, 30000)
    })
    
    return {
      route,
      visibleRoutes,
      unreadCount,
      currentUser,
      handleCommand
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  box-shadow: 2px 0 6px rgba(0,21,41,.35);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #1f2d3d;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  margin-left: 10px;
}

.sidebar-menu {
  border-right: none;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.message-badge {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
