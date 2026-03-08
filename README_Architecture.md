# 客服系统架构文档

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Dashboard  │  │   Emails    │  │  AutoReply  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   KBSearch  │  │   Settings  │  │ EmailDetail │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │    Login    │  │  Knowledge  │                               │
│  └─────────────┘  └─────────────┘                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                      后端 (Flask)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Routes                                             │   │
│  │  - POST /api/email/receive                              │   │
│  │  - POST /api/email/auto-process                        │   │
│  │  - POST /api/email/<id>/analyze                        │   │
│  │  - POST /api/email/<id>/generate-reply                 │   │
│  │  - POST /api/email/<id>/send-reply                     │   │
│  │  - DELETE /api/email/<id>                              │   │
│  │  - POST /api/knowledge-base/search                     │   │
│  │  - GET  /api/emails                                    │   │
│  │  - GET  /api/stats                                     │   │
│  │  - POST /api/auth/login                                │   │
│  │  - GET  /api/auth/profile                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ EmailService    │  │  AIService      │  │ DatabaseMgr   │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │ AuthService     │  │ CacheManager    │                       │
│  └─────────────────┘  └─────────────────┘                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      数据层                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   SQLite    │  │   MySQL     │  │  Knowledge  │             │
│  │  (默认)     │  │  (可升级)   │  │    Base     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
c:\Users\18409\OneDrive\桌面\test\
├── 📂 archive/                    # 早期归档文件
│   └── ...
│
├── 📂 archive_v2/                 # V1旧版文件
│   ├── src/                       # 旧版核心模块
│   ├── app_v2.py                  # 旧版Streamlit界面
│   └── ...
│
├── 📂 backend/                    # Flask后端
│   ├── 📂 database/               # 数据库模块
│   │   ├── __init__.py
│   │   └── db_manager.py         # 数据库管理器 (SQLite + MySQL)
│   ├── 📂 services/               # 业务服务
│   │   ├── __init__.py
│   │   ├── email_service.py      # 邮件服务
│   │   ├── ai_service.py         # AI服务
│   │   └── auth_service.py       # 认证服务
│   ├── app.py                    # Flask应用入口
│   ├── config.py                 # 配置文件
│   ├── requirements.txt          # Python依赖
│   ├── retriever.py              # 统一检索接口
│   ├── intent_classifier.py      # 意图分类器
│   ├── llm_generator.py          # LLM回复生成
│   ├── keyword_matcher.py        # 关键词匹配
│   ├── cache_manager.py          # 缓存管理
│   ├── logger.py                 # 日志系统
│   └── data_processor.py         # 数据处理器
│
├── 📂 frontend/                   # Vue3前端
│   ├── 📂 public/
│   │   └── index.html
│   ├── 📂 src/
│   │   ├── 📂 api/               # API接口
│   │   │   └── index.js
│   │   ├── 📂 router/            # 路由配置
│   │   │   └── index.js
│   │   ├── 📂 views/             # 页面组件
│   │   │   ├── Layout.vue        # 布局组件
│   │   │   ├── Dashboard.vue     # 概览页
│   │   │   ├── Emails.vue        # 邮件列表
│   │   │   ├── EmailDetail.vue   # 邮件详情
│   │   │   ├── AutoReply.vue     # 自动回复
│   │   │   ├── KnowledgeBase.vue # 知识库
│   │   │   ├── Settings.vue      # 系统设置
│   │   │   └── Login.vue         # 登录页
│   │   ├── App.vue
│   │   └── main.js
│   ├── .eslintrc.js
│   └── package.json
│
├── 📂 processed_data/             # 处理后的数据
│   ├── qa_pairs.csv              # QA对CSV
│   ├── qa_pairs.json             # QA对JSON
│   ├── llm_cache.json            # LLM缓存
│   └── 📂 logs/                  # 日志文件
│
├── 📂 scripts/                    # 工具脚本
│   └── import_data.py            # 数据导入脚本
│
├── 📂 tests/                      # 测试文件
│   └── test_api_integration.py   # API集成测试
│
├── 📄 README_Architecture.md      # 本文档
└── 📄 requirements.txt            # 项目依赖
```

## 🔌 API接口文档

### 1. 用户认证

#### 登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

#### 获取用户信息
```http
GET /api/auth/profile
Authorization: Bearer <token>

Response:
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2026-03-06T12:00:00"
  }
}
```

### 2. 邮件管理

#### 接收邮件
```http
POST /api/email/receive
Content-Type: application/json
Authorization: Bearer <token>

{
  "sender": "player@example.com",
  "subject": "充值问题",
  "content": "邮件正文...",
  "platform": "iOS",
  "app_version": "1.2.3",
  "device": "iPhone 14",
  "account_id": "12345",
  "player_name": "PlayerName"
}

Response:
{
  "success": true,
  "email_id": 1,
  "message": "Email received successfully"
}
```

#### 自动处理邮件（一键处理）
```http
POST /api/email/auto-process
Content-Type: application/json
Authorization: Bearer <token>

{
  "sender": "player@example.com",
  "subject": "充值问题",
  "content": "邮件正文...",
  "auto_send": false,      // 是否自动发送
  "use_llm": true          // 是否使用LLM
}

Response:
{
  "success": true,
  "email_id": 1,
  "reply_id": 1,
  "analysis": {
    "question_type": "充值问题",
    "urgency": "high",
    "similar_cases": [...]
  },
  "reply": {
    "content": "生成的日语回复内容...",
    "content_zh": "中文对照翻译...",
    "bilingual": {
      "japanese": "日语内容",
      "chinese": "中文内容",
      "full_text": "完整双语内容"
    },
    "model": "qwen3.5-plus"
  },
  "auto_sent": false,
  "message": "Email processed successfully (pending review)"
}
```

#### 分析邮件
```http
POST /api/email/{email_id}/analyze
Authorization: Bearer <token>

Response:
{
  "success": true,
  "email_id": 1,
  "analysis": {
    "question_type": "充值问题",
    "question_type_confidence": 0.95,
    "urgency": "high",
    "urgency_confidence": 0.88,
    "sentiment": "negative",
    "suggestions": [...]
  }
}
```

#### 生成回复
```http
POST /api/email/{email_id}/generate-reply
Content-Type: application/json
Authorization: Bearer <token>

{
  "use_llm": true
}

Response:
{
  "success": true,
  "email_id": 1,
  "reply_id": 1,
  "reply": {
    "content": "生成的日语回复...",
    "content_zh": "中文对照翻译...",
    "bilingual": {
      "japanese": "日语内容",
      "chinese": "中文内容",
      "full_text": "完整双语内容"
    },
    "model": "qwen3.5-plus",
    "confidence": 0.92
  }
}
```

#### 发送回复
```http
POST /api/email/{email_id}/send-reply
Content-Type: application/json
Authorization: Bearer <token>

{
  "content": "回复内容..."
}

Response:
{
  "success": true,
  "email_id": 1,
  "sent_at": "2026-03-06T12:00:00",
  "message": "Reply sent successfully"
}
```

#### 获取邮件列表
```http
GET /api/emails?status=new&page=1&per_page=20
Authorization: Bearer <token>

Response:
{
  "success": true,
  "emails": [...],
  "page": 1,
  "per_page": 20,
  "total": 100
}
```

#### 获取邮件详情
```http
GET /api/email/{email_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "email": {
    "id": 1,
    "sender": "...",
    "subject": "...",
    "content": "...",
    "analysis": {...},
    "reply": {...}
  }
}
```

#### 删除邮件
```http
DELETE /api/email/{email_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Email deleted successfully"
}
```

### 3. 知识库

#### 知识库搜索
```http
POST /api/knowledge-base/search
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "充值问题",
  "top_k": 5,
  "question_type": "充值问题",
  "fuzzy": true          // 是否启用模糊搜索
}

Response:
{
  "success": true,
  "query": "充值问题",
  "results": [
    {
      "question": "...",
      "answer": "...",
      "similarity": 0.95,
      "question_type": "充值问题"
    }
  ]
}
```

### 4. 统计信息

#### 获取统计信息
```http
GET /api/stats
Authorization: Bearer <token>

Response:
{
  "success": true,
  "stats": {
    "total_emails": 100,
    "new_emails": 20,
    "replied_emails": 80,
    "question_types": {...}
  }
}
```

## 🗄️ 数据库设计

### 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 邮件表 (emails)
```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    content TEXT NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    platform VARCHAR(50),
    app_version VARCHAR(50),
    device VARCHAR(100),
    account_id VARCHAR(100),
    player_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 邮件分析表 (email_analysis)
```sql
CREATE TABLE email_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    question_type VARCHAR(50),
    question_type_confidence FLOAT,
    urgency VARCHAR(20),
    urgency_confidence FLOAT,
    urgency_reason TEXT,
    sentiment VARCHAR(20),
    sentiment_confidence FLOAT,
    suggestions TEXT,
    similar_cases TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);
```

### 回复表 (replies)
```sql
CREATE TABLE replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_zh TEXT,              -- 中文对照
    generated_by VARCHAR(50),
    confidence FLOAT,
    is_auto_generated BOOLEAN DEFAULT 0,
    is_sent BOOLEAN DEFAULT 0,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);
```

### 知识库表 (knowledge_base)
```sql
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    question_type VARCHAR(50),
    platform VARCHAR(50),
    keywords TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 快速启动

### 1. 环境准备

```bash
# 安装Python依赖
cd backend
pip install -r requirements.txt

# 安装Node依赖
cd frontend
npm install
```

### 2. 配置

编辑 `backend/config.py`：

```python
# AI服务配置
OPENAI_API_KEY = "your-api-key"
OPENAI_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
LLM_MODEL = "qwen3.5-plus"

# 数据库配置
DATABASE_TYPE = "sqlite"  # 或 "mysql"
SQLITE_DB_PATH = "data/cs_system.db"

# MySQL配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'password',
    'database': 'cs_system'
}

# JWT配置
JWT_SECRET = "your-secret-key"
JWT_EXPIRE_HOURS = 24
```

### 3. 启动后端服务

```bash
cd backend
python app.py
```
后端服务将在 http://localhost:5000 启动

### 4. 启动前端服务

```bash
cd frontend
npm run serve
```
前端服务将在 http://localhost:8080 启动

### 5. 访问系统

打开浏览器访问 http://localhost:8080

默认登录账号：
- 用户名：`admin`
- 密码：`admin123`

## 🧪 运行测试

```bash
# 运行API集成测试
python tests/test_api_integration.py
```

## 📊 系统特性

### ✅ 已实现功能
- [x] 前后端分离架构 (Vue3 + Flask)
- [x] JWT用户认证与权限管理
- [x] 邮件自动接收与解析
- [x] AI意图分类与紧急度判断
- [x] 知识库检索与相似案例推荐
- [x] 模糊搜索支持
- [x] LLM自动生成中日双语客服回复
- [x] 邮件自动处理流程
- [x] 邮件删除功能
- [x] SQLite数据库支持
- [x] MySQL升级接口
- [x] 缓存机制降低API成本
- [x] 操作日志记录
- [x] 完整的API测试覆盖

### 🔄 处理流程
1. 接收邮件 → 2. 解析内容 → 3. 意图分类 → 4. 紧急度判断 → 5. 检索相似案例 → 6. 生成双语回复 → 7. 人工审核/自动发送

## 🛡️ 安全特性

- JWT Token认证
- 密码BCrypt加密存储
- API访问权限控制
- 前端路由守卫
- 请求超时处理

## 📝 更新日志

### 2026-03-06
- ✅ 添加用户登录认证功能
- ✅ 实现中日双语回复生成
- ✅ 添加知识库模糊搜索
- ✅ 添加邮件删除功能
- ✅ 修复邮件详情页面导航问题
- ✅ 修复处理建议乱码问题
- ✅ 修复LLM超时问题
- ✅ 修复后端AI服务配置
- ✅ 修复知识库搜索接口
- ✅ 所有API测试通过
- ✅ 归档旧版文件

---

**系统状态**: ✅ 所有功能正常运行

**默认账号**: admin / admin123
