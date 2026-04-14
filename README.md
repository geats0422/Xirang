# Xirang 息壤

> 投喂一点知识，生长无限闯关路径。

Xirang（息壤）是一个 AI 驱动的游戏化学习平台。上传学习材料，AI 自动解析生成个性化题库，通过无尽深渊、速答生存、知识草稿三种模式进行挑战，获得经验值和代币奖励。

## 项目状态

**核心闭环已完整实现**：上传 → 解析 → 题库生成 → 答题 → 结算 → 奖励 → 商店

**待完成**：支付网关集成（Creem/Stripe）

---

## 技术架构

### 前端

- **框架**: Vue 3 + TypeScript + Vite
- **路由**: Vue Router 4
- **状态**: Composition API + 本地存储
- **测试**: Vitest + @vue/test-utils
- **国际化**: vue-i18n（11 种语言）
- **主题**: CSS 变量驱动，支持 light/dark/system

### 后端

- **框架**: FastAPI + SQLAlchemy 2.0 (async)
- **数据库**: PostgreSQL + pgvector
- **任务队列**: 自定义 Job + Worker 轮询
- **AI 解析**: PageIndex + OpenAI/NVIDIA
- **文档解析**: MinerU (PDF)
- **包管理**: uv

---

## 核心功能闭环

### 1. 文档上传与解析 ✅

| 组件 | 状态 | 说明 |
|------|------|------|
| 前端上传 | ✅ | `uploadDocument()` 调用 `/api/v1/documents/upload` |
| 文件存储 | ✅ | 支持 local/S3 模式 |
| 异步解析 | ✅ | Worker 自动处理 ingestion job |
| 状态追踪 | ✅ | processing → indexing → generating → ready |
| PageIndex 索引 | ✅ | 文档向量化索引，支持语义检索 |
| 题库生成 | ✅ | LLM 自动生成选择题、填空题、判断题 |

### 2. 游戏模式 ✅

支持三种答题模式，全部接入真实后端 API：

| 模式 | 路由 | 状态 | 特点 |
|------|------|------|------|
| 无尽深渊 | `/library/game-modes/endless-abyss` | ✅ | 多楼层闯关，连击加成 |
| 速答生存 | `/library/game-modes/speed-survival` | ✅ | 限时挑战，三种路线 |
| 知识草稿 | `/library/game-modes/knowledge-draft` | ✅ | 组卡策略，知识点覆盖 |
| 错题复习 | `/library/game-modes/review` | ✅ | 基于错题集的智能复习 |

### 3. Run 生命周期 ✅

```
创建 Run → 获取题目 → 答题 → 提交 → 结算 → 奖励发放
```

- **创建**: `POST /api/v1/runs`
- **答题**: `POST /api/v1/runs/{id}/answers`
- **结算**: 自动计算 XP/COIN 奖励
- **复活**: 支持复活盾道具

### 4. 经济系统 ✅

| 功能 | API | 状态 |
|------|-----|------|
| 钱包余额 | `GET /api/v1/shop/balance` | ✅ |
| 商品列表 | `GET /api/v1/shop/items` | ✅ |
| 购买道具 | `POST /api/v1/shop/purchase` | ✅ |
| 背包管理 | `GET /api/v1/shop/inventory` | ✅ |
| 交易记录 | `GET /api/v1/shop/ledger` | ✅ |
| 使用道具 | `POST /api/v1/shop/use-item` | ✅ |

资产类型：COIN（代币）、XP（经验值）

### 5. 每日任务 ✅

- `GET /api/v1/quests` - 获取今日任务
- `POST /api/v1/quests/{id}/claim` - 领取奖励
- 自动追踪答题进度、登录等事件

### 6. 排行榜 ✅

- `GET /api/v1/leaderboard` - 周榜/月榜/总榜
- 支持 XP、答题正确率等多维度排行

### 7. 错题与反馈 ✅

- 错题自动收录
- 支持题目反馈（错误报告、建议）
- AI 解析错题原因

---

## 页面路由

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | 着陆页 | 产品介绍 |
| `/login` | 登录页 | 邮箱/社交登录 |
| `/home` | 主页 | 文档上传、最近地城 |
| `/library` | 书库 | 文档列表、进度追踪 |
| `/library/game-modes/*` | 游戏模式 | 三种答题模式 |
| `/quests` | 每日任务 | 任务列表、奖励领取 |
| `/shop` | 商店 | 道具购买、背包 |
| `/leaderboard` | 排行榜 | 多维度排行 |
| `/settings` | 设置 | 个人资料、偏好 |
| `/pricing` | 定价页 | 代币包、订阅方案 |

---

## 本地开发

### 环境要求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ (需 pgvector 扩展)
- uv (`pip install uv`)

### 启动后端

```bash
cd backend
uv venv .venv
uv sync --extra dev

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 DATABASE_URL, SECRET_KEY 等

# 初始化数据库
uv run alembic upgrade head

# 启动服务
uv run uvicorn app.main:app --reload --port 8000
```

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：`http://localhost:5173`

### 启动 Worker

```bash
cd backend
uv run python -m app.workers.main
```

---

## 环境变量

### 后端 (`backend/.env`)

```bash
# 必需
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/xirang
SECRET_KEY=your-secret-key

# AI 服务（至少配置一个）
OPENAI_API_KEY=sk-...
NVIDIA_API_KEY=nvapi-...

# PageIndex（可选，文档索引）
PAGEINDEX_URL=http://localhost:8080

# 存储
STORAGE_MODE=local  # 或 s3
UPLOAD_DIR=.data/uploads

# CORS
CORS_ORIGINS=http://localhost:5173,https://your-frontend.com
```

### 前端 (`frontend/.env`)

```bash
# 开发环境（使用 Vite 代理）
VITE_API_BASE_URL=
VITE_API_PROXY_TARGET=http://localhost:8000

# 生产环境（直接访问后端）
# VITE_API_BASE_URL=https://api.xirang.app/api/v1
```

---

## 部署

### 后端 (Render)

1. 创建 Web Service，选择 Docker 或 Python 3.11
2. 设置环境变量（`SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`）
3. 配置健康检查：`/health`
4. 免费层注意：15 分钟无活动会休眠，建议配置 cron-job 定期 ping

### 前端 (Vercel)

```bash
cd frontend
vercel --prod
```

配置 `vercel.json` 重写规则：
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-api.com/api/$1" },
    { "source": "/health", "destination": "https://your-api.com/health" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 质量检查

### 后端

```bash
cd backend
uv run ruff check app tests
uv run mypy app
uv run pytest -q --tb=short
```

### 前端

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

---

## 项目结构

```
Xirang/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # 组件
│   │   ├── composables/  # 组合式函数
│   │   ├── pages/        # 页面
│   │   └── ...
│   └── vercel.json
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/       # API 路由
│   │   ├── services/     # 业务逻辑
│   │   ├── repositories/ # 数据访问
│   │   ├── workers/      # 异步任务
│   │   └── db/models/    # 数据模型
│   └── tests/
└── docs/                  # 文档
```

---

## 下一步

### Phase 2: 商业化

- [ ] **支付网关集成**
  - Creem/Stripe 接入
  - 代币包购买
  - 订阅方案（Free/Super）

- [ ] **高级功能**
  - 团队协作空间
  - 学习路径定制
  - AI 导师对话

---

## 许可证

MIT
