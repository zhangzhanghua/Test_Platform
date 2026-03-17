# Test Platform - 测试管理平台

一站式测试管理平台，涵盖用例管理、测试执行、缺陷跟踪、环境管理、通知推送等核心功能，支持动态 RBAC 权限控制。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + ECharts + Vite |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2 |
| 数据库 | PostgreSQL 16 |
| 缓存/消息 | Redis 7 |
| 任务队列 | Celery |
| 反向代理 | Nginx |
| 容器化 | Docker Compose |

## 功能模块

### 仪表盘
- 项目数、执行总数、通过/失败统计卡片
- 最近执行趋势柱状图（ECharts）

### 项目管理
- 项目 CRUD
- 项目关联测试套件、环境、缺陷

### 用例管理
- 测试套件管理（按项目分组）
- 用例 CRUD（标题、描述、优先级 P0-P3、标签、脚本路径）
- 分类树：侧边栏按项目展示多级分类节点，支持右键新增子节点/重命名/删除
- 按分类节点过滤用例

### 测试执行
- 选择用例批量执行
- Celery 异步执行任务
- WebSocket 实时推送执行日志
- 执行结果记录（通过/失败/错误/跳过）

### 缺陷管理
- 缺陷 CRUD，支持表格行内编辑（标题、严重程度、状态、指派人）
- 状态流转：待处理 → 处理中 → 已修复 → 已验证 → 已关闭（含拒绝分支）
- 严重程度：严重 / 主要 / 次要 / 轻微
- 评论系统
- 附件上传/下载
- 统计图表：严重程度饼图 + 状态分布柱状图
- 分类树：侧边栏按项目展示多级分类节点

### 环境管理
- 环境配置（名称、Base URL、变量 JSON）
- 按项目分组

### 测试报告
- 执行结果汇总
- 通过率统计

### 通知管理
- 支持邮件（SMTP）和飞书 Webhook 两种通知渠道
- 按项目配置通知渠道
- 执行完成自动触发通知

### Webhooks
- CI/CD 触发接口
- Token 鉴权
- 绑定测试套件和环境，外部系统可通过 Webhook 触发测试执行

### 系统管理（动态 RBAC）
- **用户管理**：用户列表、角色分配、启用/禁用
- **角色管理**：角色 CRUD、角色-菜单权限配置（Tree 勾选）
- **菜单管理**：菜单树 CRUD（名称、路径、图标、排序）
- 预置角色：管理员、项目经理、服务端开发、QA、Android 开发、iOS 开发、Web 开发、产品、UI、观察者
- 前端菜单根据用户角色动态渲染

## 项目结构

```
Test_Platform/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── auth.py       # 认证（注册/登录/me）
│   │   │   ├── bugs.py       # 缺陷管理
│   │   │   ├── deps.py       # 依赖注入（鉴权、角色校验）
│   │   │   ├── environments.py
│   │   │   ├── executions.py # 测试执行
│   │   │   ├── notify.py     # 通知管理
│   │   │   ├── projects.py   # 项目管理
│   │   │   ├── system.py     # 系统管理（RBAC）
│   │   │   ├── tab_nodes.py  # 分类树节点
│   │   │   ├── testcases.py  # 用例管理
│   │   │   ├── users.py      # 用户管理
│   │   │   ├── webhooks.py   # Webhook 管理
│   │   │   └── ws.py         # WebSocket 实时日志
│   │   ├── core/             # 核心配置
│   │   │   ├── config.py     # 应用配置
│   │   │   ├── database.py   # 数据库连接
│   │   │   ├── pubsub.py     # Redis 发布订阅
│   │   │   └── security.py   # JWT + 密码哈希
│   │   ├── models/
│   │   │   └── models.py     # SQLAlchemy 模型
│   │   ├── schemas/
│   │   │   └── schemas.py    # Pydantic 数据模型
│   │   ├── services/
│   │   │   └── notify.py     # 通知发送服务
│   │   ├── tasks/
│   │   │   ├── celery_app.py # Celery 配置
│   │   │   └── runner.py     # 测试执行 Worker
│   │   └── main.py           # FastAPI 入口 + 种子数据
│   ├── alembic/              # 数据库迁移
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── CategoryTree.tsx  # 通用分类树组件
│   │   ├── layouts/
│   │   │   └── MainLayout.tsx    # 主布局（侧边栏+分类树）
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx     # 仪表盘
│   │   │   ├── ProjectsPage.tsx  # 项目管理
│   │   │   ├── TestCasesPage.tsx # 用例管理
│   │   │   ├── ExecutionsPage.tsx# 测试执行
│   │   │   ├── BugsPage.tsx      # 缺陷管理
│   │   │   ├── EnvironmentsPage.tsx
│   │   │   ├── ReportsPage.tsx   # 测试报告
│   │   │   ├── NotifyPage.tsx    # 通知管理
│   │   │   ├── WebhooksPage.tsx  # Webhook 管理
│   │   │   ├── SystemPage.tsx    # 系统管理
│   │   │   └── LoginPage.tsx     # 登录页
│   │   ├── services/
│   │   │   └── api.ts            # Axios 实例
│   │   ├── App.tsx               # 路由配置
│   │   └── main.tsx              # 入口
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   └── nginx/
│       └── default.conf          # Nginx 反向代理配置
└── docker-compose.yml
```

## 快速开始

### 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0

### 一键启动

```bash
git clone https://github.com/zhangzhanghua/Test_Platform.git
cd Test_Platform
docker compose up -d --build
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | 统一入口（推荐） |
| Frontend | 3000 | 前端开发服务 |
| Backend | 8000 | 后端 API |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存/消息队列 |

### 访问

- 前端页面：http://localhost（通过 Nginx）或 http://localhost:3000
- API 文档：http://localhost:8000/docs（Swagger UI）
- 健康检查：http://localhost:8000/health

### 默认账户

首次启动时系统会自动初始化种子数据：
- 注册第一个用户后，在数据库中该用户会被分配默认角色
- 预置 10 个角色和对应的菜单权限映射

## API 概览

| 模块 | 前缀 | 主要端点 |
|------|------|----------|
| 认证 | `/api/v1/auth` | POST `/register`, `/login`, GET `/me` |
| 项目 | `/api/v1/projects` | CRUD |
| 用例 | `/api/v1/testcases` | 套件 CRUD + 用例 CRUD |
| 执行 | `/api/v1/executions` | 创建执行、查看结果 |
| 缺陷 | `/api/v1/bugs` | CRUD + 状态流转 + 评论 + 附件 + 统计 |
| 环境 | `/api/v1/environments` | CRUD |
| 通知 | `/api/v1/notify` | 渠道 CRUD + 测试发送 |
| Webhook | `/api/v1/webhooks` | CRUD + 触发执行 |
| 系统 | `/api/v1/system` | 角色/菜单/用户角色 管理 |
| 分类树 | `/api/v1/tab-nodes` | 树节点 CRUD |
| WebSocket | `/ws/executions/{id}/logs` | 实时执行日志 |

## 数据模型

```
User ──┬── SysRole (多对多, sys_user_role)
       │      └── SysMenu (多对多, sys_role_menu)
       │
Project ──┬── TestSuite ── TestCase ── TestResult
          ├── Environment              │
          ├── Bug ──┬── BugComment     │
          │         └── BugAttachment  │
          └── TabNode (分类树)    TestExecution
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/test_platform` | 异步数据库连接 |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 连接 |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery Broker |
| `SECRET_KEY` | `change-me-in-production` | JWT 签名密钥 |
| `SMTP_HOST` | - | 邮件服务器地址 |
| `SMTP_PORT` | `465` | 邮件服务器端口 |
| `SMTP_USER` | - | 邮件账号 |
| `SMTP_PASSWORD` | - | 邮件密码 |

## 常用命令

```bash
# 启动所有服务
docker compose up -d --build

# 仅重建前端
docker compose up -d --build frontend

# 仅重建后端
docker compose up -d --build backend celery-worker

# 查看后端日志
docker logs -f test_platform-backend-1

# 进入数据库
docker exec -it test_platform-db-1 psql -U postgres -d test_platform

# 停止所有服务
docker compose down

# 停止并清除数据卷
docker compose down -v
```

## License

MIT
