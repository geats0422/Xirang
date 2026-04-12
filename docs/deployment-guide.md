# 息壤（Xirang）部署指南：Vercel + Render + Supabase

本指南针对当前 monorepo 结构（`frontend/` + `backend/`），将前端部署到 Vercel、后端部署到 Render、数据库使用 Supabase。

---

## 架构总览

```
用户浏览器
    │
    ├── 静态资源 (HTML/CSS/JS) ──→ Vercel (CDN)
    │
    └── /api/v1/* 请求 ──→ Render Web Service (FastAPI)
                              │
                              ├── Supabase PostgreSQL (远程托管，原生 pgvector)
                              └── Background Worker (文档处理 + 题库生成)
```

| 组件 | 平台 | 服务类型 | 说明 |
|---|---|---|---|
| 前端 | Vercel | Static Site | Vue 3 + Vite SPA |
| 后端 API | Render | Web Service (Free) | FastAPI + uvicorn，休眠型 |
| Worker | Render | Background Worker | 文档摄取 + 题库生成 |
| 数据库 | Supabase | PostgreSQL | 托管 PostgreSQL + pgvector |

---

## 第一部分：Supabase 数据库

### 1.1 为什么选 Supabase 而不是 Render PostgreSQL

| 对比项 | Supabase（免费版） | Render PostgreSQL |
|---|---|---|
| pgvector 支持 | 原生内置 | 不确定，需手动安装 |
| 免费版有效期 | **永不过期** | 30 天后删除 |
| 免费版存储 | 500MB | 256MB |
| 连接方式 | 直连 / 连接池 | 直连 |
| 备份 | 每日自动备份（Pro） | 付费版有备份 |
| 管理界面 | 完整 Dashboard + SQL 编辑器 | 仅命令行 |

> **为什么不选 Cloudflare D1**：D1 是 SQLite 数据库，不兼容 PostgreSQL。当前项目使用 asyncpg 驱动、pgvector 扩展、PostgreSQL 特有语法，迁移到 D1 需要大量代码改造。

### 1.2 创建 Supabase 项目

1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 点击 **New Project**
3. 配置：
   - **Name**: `xirang`
   - **Database Password**: 设置一个强密码并保存
   - **Region**: 选离你最近的（如 Northeast Asia (Tokyo)）
   - **Plan**: Free
4. 等待项目初始化完成（约 2 分钟）

### 1.3 获取连接串

在 Supabase Dashboard → 项目 → **Connect** 按钮：

**直连模式**（推荐用于 Render 持久服务）：
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

**事务模式**（如果 Render 不支持 IPv6）：
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

> 项目的 `build_async_database_url()` 会自动将 `postgresql://` 转换为 `postgresql+asyncpg://`，无需手动修改。

### 1.4 启用 pgvector 扩展

Supabase 默认已包含 pgvector。在 SQL Editor 中确认：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.5 连接池注意事项

Render 的持久服务（Web Service / Worker）适合使用 **Session 模式（端口 5432）** 或**直连**。如果 Render 环境不支持 IPv6，使用 Supavisor Pooler 的 Session 模式。

如果使用**事务模式（端口 6543）**，需要在 `app/db/session.py` 中添加 `poolclass=NullPool`：

```python
# 仅在事务模式下需要
from sqlalchemy.pool import NullPool

engine = create_async_engine(url, poolclass=NullPool)
```

---

## 第二部分：后端部署到 Render

### 2.1 创建 `render.yaml`（Blueprint）

在仓库**根目录**创建 `render.yaml`：

```yaml
services:
  # ===== 后端 API =====
  - type: web
    name: xirang-api
    runtime: python
    plan: free
    region: singapore
    branch: dev
    rootDir: backend
    buildCommand: pip install uv && uv sync --frozen --no-dev && uv cache prune
    startCommand: uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: CORS_ORIGINS
        value: "https://你的vercel域名.vercel.app"
      - key: FRONTEND_BASE_URL
        value: "https://你的vercel域名.vercel.app"
      - key: STORAGE_MODE
        value: local
      - key: UPLOAD_DIR
        value: /tmp/xirang-uploads
      - key: PAGEINDEX_MOCK_FALLBACK
        value: "true"
      - key: NVIDIA_API_KEY
        sync: false
      - key: GITHUB_CLIENT_ID
        sync: false
      - key: GITHUB_CLIENT_SECRET
        sync: false
      - key: GITHUB_CALLBACK_URL
        value: "https://你的render-api域名.onrender.com/api/v1/auth/oauth/github/callback"
      - key: GOOGLE_CLIENT_ID
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false
      - key: GOOGLE_CALLBACK_URL
        value: "https://你的render-api域名.onrender.com/api/v1/auth/oauth/google/callback"
      - key: MICROSOFT_CLIENT_ID
        sync: false
      - key: MICROSOFT_CLIENT_SECRET
        sync: false
      - key: MICROSOFT_TENANT_ID
        value: common
      - key: MICROSOFT_CALLBACK_URL
        value: "https://你的render-api域名.onrender.com/api/v1/auth/oauth/microsoft/callback"

  # ===== Background Worker =====
  - type: worker
    name: xirang-worker
    runtime: python
    plan: starter
    region: singapore
    branch: dev
    rootDir: backend
    buildCommand: pip install uv && uv sync --frozen --no-dev && uv cache prune
    startCommand: uv run python -m app.workers.main
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        sync: false
      - key: STORAGE_MODE
        value: local
      - key: UPLOAD_DIR
        value: /tmp/xirang-uploads
      - key: PAGEINDEX_MOCK_FALLBACK
        value: "true"
      - key: NVIDIA_API_KEY
        sync: false
      - key: PAGEINDEX_URL
        value: "http://localhost:8080"
```

**关键变化**：
- 不再使用 `fromDatabase`，`DATABASE_URL` 改为 `sync: false`（在 Dashboard 手动填写 Supabase 连接串）
- 移除了 `databases` 部分
- `startCommand` 中加入了 `alembic upgrade head` 自动迁移

### 2.2 配置 DATABASE_URL

在 Render Dashboard 中为 API 和 Worker **分别**设置 `DATABASE_URL`：

```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

> 两个服务需要填写**相同的** DATABASE_URL。

### 2.3 关键配置说明

| 配置项 | 说明 |
|---|---|
| `rootDir: backend` | Render 从 monorepo 的 `backend/` 子目录构建 |
| `buildCommand` | 安装 uv → 同步依赖 → 清理缓存 |
| `startCommand` (Web) | 先运行 Alembic 迁移，再启动 uvicorn |
| `startCommand` (Worker) | 直接运行 worker 长轮询进程 |
| `healthCheckPath: /health` | Render 通过此路径检测服务健康状态 |
| `sync: false` | 标记为 secret，在 Dashboard 手动填写 |

### 2.4 Worker 架构说明

当前 Worker 是一个**长轮询进程**（非 Celery），它：
- 轮询 `jobs` 表中的待处理任务
- 执行 `document_ingestion`（文档解析 → PageIndex 索引 → LLM 题库生成）
- 执行 `document_failed_cleanup`（失败文档清理）

**注意**：Worker 中依赖了 PageIndex 和 MinerU 两个外部服务：
- **PageIndex**：Worker 进程没有 mock server，`PAGEINDEX_URL` 需要指向真实的 PageIndex 实例
- **MinerU**：文档解析服务。如果不可用，仅支持 markdown/txt 格式上传
- 如果暂时不需要文档处理功能，可以**先不部署 Worker**，只部署 API

### 2.5 Render 部署步骤

1. 将 `render.yaml` 提交到仓库根目录
2. 在 Render Dashboard → **Blueprints** → **New Blueprint Instance**
3. 连接 GitHub 仓库
4. Render 会读取 `render.yaml`，自动创建 API + Worker 两个服务
5. 在 Dashboard 中填写环境变量：
   - `DATABASE_URL`：粘贴 Supabase 连接串
   - `NVIDIA_API_KEY`、OAuth credentials 等 secret 变量
6. 首次部署成功后，Alembic 迁移会在启动时自动执行

---

## 第三部分：前端部署到 Vercel

### 3.1 创建 `vercel.json`

在 `frontend/` 目录创建 `vercel.json`：

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://你的render-api域名.onrender.com/api/$1" },
    { "source": "/health", "destination": "https://你的render-api域名.onrender.com/health" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**关键说明**：
- 第一条 rewrite：将 `/api/*` 代理到后端（替代开发时的 Vite proxy）
- 第二条 rewrite：健康检查代理
- 第三条 rewrite：SPA fallback（Vue Router history 模式必须）

### 3.2 配置环境变量

在 Vercel 项目设置 → Environment Variables 中添加：

| 变量 | 值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | （留空） | 通过 vercel.json rewrite 代理 |
| `VITE_ENABLE_BACKEND_HEALTH_CHECK` | `true` | 启用后端连通性检测 |

### 3.3 Vercel 部署步骤

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. **Add New** → **Project**
3. 导入 GitHub 仓库 `geats0422/Xirang`
4. 配置：
   - **Framework Preset**: `Vite`
   - **Root Directory**: 点击 Edit → 选择 `frontend`
   - **Build Command**: `npm run build`（默认自动检测）
   - **Output Directory**: `dist`（默认自动检测）
5. 在 Environment Variables 中添加上面的变量
6. 点击 **Deploy**

### 3.4 更新 CORS 配置

部署成功后，Vercel 会分配一个域名（如 `xirang.vercel.app`）。需要回 Render 更新：

```
CORS_ORIGINS=https://xirang.vercel.app
FRONTEND_BASE_URL=https://xirang.vercel.app
```

### 3.5 更新 OAuth 回调 URL

在 GitHub/Google/Microsoft 的 OAuth 应用设置中，将回调 URL 更新为：

```
https://你的render-api域名.onrender.com/api/v1/auth/oauth/github/callback
https://你的render-api域名.onrender.com/api/v1/auth/oauth/google/callback
https://你的render-api域名.onrender.com/api/v1/auth/oauth/microsoft/callback
```

---

## 第四部分：自定义域名（可选）

### 4.1 Vercel 域名

1. Vercel Dashboard → 项目 → Settings → Domains
2. 添加你的域名（如 `xirang.app`）
3. 按提示在域名注册商添加 CNAME 记录

### 4.2 Render 域名

1. Render Dashboard → xirang-api → Settings
2. 添加自定义域名（如 `api.xirang.app`）
3. 添加 CNAME 记录指向 Render 提供的目标

### 4.3 更新所有 URL

自定义域名生效后，全局替换以下配置：

| 位置 | 变量 | 值 |
|---|---|---|
| Vercel `vercel.json` | rewrite destination | `https://api.xirang.app/api/$1` |
| Render | `CORS_ORIGINS` | `https://xirang.app` |
| Render | `FRONTEND_BASE_URL` | `https://xirang.app` |
| Render | `*_CALLBACK_URL` | `https://api.xirang.app/api/v1/auth/oauth/*/callback` |
| OAuth Providers | Callback URL | 同上 |
| Vercel | `VITE_APP_BASE_URL` | `https://xirang.app` |

---

## 第五部分：Free API 冷启动优化

Free 等级的 API 在 15 分钟无请求后会休眠，冷启动需 30-60s。以下从**前端代码**和**外部保活**两个层面优化。

### 5.1 前端预唤醒（已内置）

代码中已实现以下优化：

**1. 页面加载时静默唤醒**
- 登录页 `onMounted` 时自动 ping `/health`
- 用户填写表单的几秒内，API 已经唤醒完成
- `src/api/wakeup.ts` — 唤醒工具，带状态缓存避免重复 ping

**2. OAuth 前预唤醒**
- 用户点击 GitHub/Google/Microsoft 登录按钮时
- 先 `await wakeupServer()` 确保 API 在线
- 然后再跳转到 OAuth 授权页
- 这样回调时 API 一定是在线的，消除 OAuth 回调超时风险

**3. 唤醒状态按钮禁用**
- 唤醒期间社交登录按钮显示 disabled 状态
- 防止用户在 API 冷启动过程中重复点击

### 5.2 外部 Cron 保活（推荐配置）

用免费的外部监控服务每 14 分钟 ping 一次 Render 的 `/health`，让 API 始终不休眠。

**方案 A：cron-job.org（推荐，零代码）**

1. 注册 [cron-job.org](https://cron-job.org)
2. 创建 Job：
   - **Title**: `xirang-keep-alive`
   - **URL**: `https://你的render-api域名.onrender.com/health`
   - **Schedule**: Every `14` minutes
   - **HTTP Method**: GET
3. 保存并启用

**方案 B：UptimeRobot（监控 + 保活二合一）**

1. 注册 [UptimeRobot](https://uptimerobot.com)
2. 创建 Monitor：
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `Xirang API`
   - **URL**: `https://你的render-api域名.onrender.com/health`
   - **Monitoring Interval**: 5 分钟（免费版最短）
3. 保存

**方案 C：GitHub Actions（适合开发者）**

在仓库中创建 `.github/workflows/keep-alive.yml`：

```yaml
name: Keep Render Alive
on:
  schedule:
    - cron: "*/14 * * * *"
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render API
        run: |
          curl -sf --max-time 90 "https://你的render-api域名.onrender.com/health" || true
```

> 注意：GitHub Actions 的 cron 可能有 5-10 分钟延迟。如果需要精确定时，用方案 A 或 B。

### 5.3 优化效果总结

| 优化层 | 方案 | 冷启动 | OAuth 风险 | 成本 |
|---|---|---|---|---|
| 无优化 | — | 30-60s 延迟 | 回调可能超时 | $0 |
| 前端预唤醒 | 代码内置 | 用户感知 ~0s | 已消除 | $0 |
| 外部保活 | cron-job.org | 消除 | 消除 | $0 |
| **全部启用** | **前端 + 保活** | **消除** | **消除** | **$0** |

---

## 第六部分：完整部署检查清单

### 部署前

- [ ] `render.yaml` 已提交到仓库根目录
- [ ] `frontend/vercel.json` 已提交（rewrite 目标指向 Render URL）
- [ ] 准备好 OAuth 应用凭据（GitHub/Google/Microsoft Client ID + Secret）
- [ ] 准备好 NVIDIA API Key（或 OpenAI Key）

### Supabase

- [ ] 项目创建成功
- [ ] pgvector 扩展已启用
- [ ] 获取了连接串（Session 模式或直连）
- [ ] 在 SQL Editor 中测试过连接

### Render 部署

- [ ] 通过 Blueprint 创建了 API (Free) + Worker (Starter) 两个服务
- [ ] 在 Dashboard 填写了 `DATABASE_URL`（Supabase 连接串）
- [ ] 填写了所有 `sync: false` 的 secret 环境变量
- [ ] 首次部署成功（Alembic 迁移在启动时自动执行）
- [ ] 访问 `https://你的api.onrender.com/health` 返回 `{"status": "ok"}`

### Vercel 部署

- [ ] Root Directory 设置为 `frontend`
- [ ] `vercel.json` 中的 rewrite 目标已更新为 Render URL
- [ ] 环境变量已配置
- [ ] 访问 Vercel 域名可看到着陆页
- [ ] 直接访问 `/login` 等 SPA 路由不会 404

### 冷启动优化

- [ ] 前端 `wakeupServer()` 在登录页加载时自动执行
- [ ] OAuth 按钮点击前预唤醒 API
- [ ] 已配置外部 cron 保活（cron-job.org / UptimeRobot / GitHub Actions）

### 联调验证

- [ ] 前端 `/api/v1/health` 能通过 rewrite 到达后端
- [ ] 注册/登录接口正常（Supabase 数据库可写入）
- [ ] OAuth 登录流程正常（GitHub/Google/Microsoft）
- [ ] `CORS_ORIGINS` 已包含 Vercel 域名

---

## 第七部分：常见问题

### Q1: Supabase vs Render PostgreSQL vs Cloudflare D1

| 对比项 | Supabase | Render PostgreSQL | Cloudflare D1 |
|---|---|---|---|
| 数据库类型 | PostgreSQL | PostgreSQL | **SQLite（不兼容）** |
| pgvector | 原生支持 | 需手动安装 | 不支持 |
| 免费版 | 500MB，永不过期 | 256MB，30 天过期 | 5GB，永不过期 |
| 连接池 | 内置 Supavisor | 无 | N/A |
| 代码改动 | 零 | 零 | **大量改造** |

### Q2: API 用 Free 等级有什么影响？

- **休眠**：15 分钟无请求会自动休眠，冷启动 ~30-60s
- **CPU 较弱**：Free 是 0.1 CPU（Starter 是 0.5），RAM 都是 512MB
- **已内置优化**：前端在页面加载和 OAuth 按钮点击时自动预唤醒 API
- **建议**：配置外部 cron 保活（cron-job.org），让 API 始终在线

### Q3: 部署后 Worker 报 PageIndex 连接失败？

Worker 中的 `PageIndexBackend` 需要真实的 PageIndex 服务。解决方案：

1. **暂时禁用文档处理**：不部署 Worker，API 正常运行但不处理文档
2. **部署 PageIndex**：在 Render 上另开一个 Web Service 运行 PageIndex
3. **使用 mock**：修改 Worker 代码使用 mock server（仅测试用途）

### Q4: 数据库连接串格式不匹配？

Supabase 提供的连接串格式为 `postgresql://...`，项目需要 `postgresql+asyncpg://`。`app/db/session.py` 中的 `build_async_database_url()` 会自动转换，无需手动修改。

### Q5: Supabase 连接超时？

如果 Render 环境不支持 IPv6，直连会失败。改用 Supavisor Pooler 的 Session 模式连接串（端口 5432），该模式同时支持 IPv4 和 IPv6。

### Q6: 上传的文件存在哪里？

当前 `STORAGE_MODE=local`，文件存储在容器的 `/tmp/xirang-uploads`。注意 Render 容器的临时文件系统在重启后会丢失。生产环境建议：
- 使用 S3 兼容的对象存储（需要实现 `s3` storage mode）
- 或 Render 的持久磁盘（需付费计划）

### Q7: Vercel 部署后刷新页面 404？

确保 `vercel.json` 中有 SPA fallback rewrite：
```json
{ "source": "/(.*)", "destination": "/index.html" }
```

### Q8: API 代理不工作？

检查 `vercel.json` 中的 rewrite 目标 URL 是否正确（必须是 Render 分配的完整域名，包含 `https://`）。

---

## 第八部分：费用估算

| 服务 | 平台 | 实例类型 | 月费用 |
|---|---|---|---|
| 前端 | Vercel | Hobby（免费） | $0 |
| API | Render | Web Service Free (512MB, 休眠型) | $0 |
| Worker | Render | Background Worker Starter (512MB) | $7 |
| PostgreSQL | Supabase | Free (500MB) | $0 |
| **合计** | | | **$7/月** |

> **早期验证阶段推荐配置**：API 使用 Free 等级（15 分钟无请求休眠，冷启动 ~30-60s），Worker 使用 Starter（始终在线），数据库用 Supabase 免费版。
>
> **升级路径**：用户量上来后将 API 从 Free 升级到 Starter（$7/月），总费用变为 $14/月，API 始终在线、CPU 从 0.1 提升到 0.5。
