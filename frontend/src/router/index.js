import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../views/Layout.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { public: true }
    },
    {
        path: '/',
        component: Layout,
        redirect: '/dashboard',
        meta: { requiresAuth: true },
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue'),
                meta: { title: '概览', icon: 'HomeFilled', requiresAuth: true }
            },
            {
                path: 'emails',
                name: 'Emails',
                component: () => import('../views/Emails.vue'),
                meta: { title: '邮件管理', icon: 'Message', requiresAuth: true }
            },
            {
                path: 'email/:id',
                name: 'EmailDetail',
                component: () => import('../views/EmailDetail.vue'),
                meta: { title: '邮件详情', hidden: true, requiresAuth: true }
            },
            {
                path: 'auto-reply',
                name: 'AutoReply',
                component: () => import('../views/AutoReply.vue'),
                meta: { title: '自动回复', icon: 'Promotion', requiresAuth: true }
            },
            {
                path: 'knowledge-base',
                name: 'KnowledgeBase',
                component: () => import('../views/KnowledgeBase.vue'),
                meta: { title: '知识库', icon: 'Collection', requiresAuth: true }
            },
            {
                path: 'settings',
                name: 'Settings',
                component: () => import('../views/Settings.vue'),
                meta: { title: '系统设置', icon: 'Setting', requiresAuth: true }
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    
    if (to.meta.requiresAuth && !token) {
        // 需要登录但未登录，跳转到登录页
        next('/login')
    } else if (to.path === '/login' && token) {
        // 已登录但访问登录页，跳转到首页
        next('/')
    } else {
        next()
    }
})

export default router
