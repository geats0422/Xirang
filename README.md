# Xirang Monorepo

息壤项目当前采用前后端同仓结构：

- `frontend/`: Vue 3 + TypeScript + Vite
- `backend/`: FastAPI + SQLAlchemy + PostgreSQL

本文档以“当前代码真实状态”为准，包含：架构说明、启动步骤、环境变量、前后端联通方式、Phase-1 完成度盘点与验证命令。

## 1. 仓库结构

```text
Xirang/
├─ frontend/                    # Vue 3 应用
│  ├─ src/
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ composables/
│  │  └─ api/
│  ├─ vite.config.ts
│  └─ package.json
├─ backend/                     # FastAPI 服务
│  ├─ app/
│  │  ├─ api/v1/
│  │  ├─ services/
│  │  ├─ repositories/
│  │  ├─ workers/
│  │  └─ db/models/
│  ├─ tests/
│  ├─ pyproject.toml
│  └─ .env.example
├─ docs/
│  └─ specs/2026-03-16-backend-v1-design.md
└─ AGENTS.md
```

## 2. 技术架构

### 前端

- 框架：Vue 3 + Vue Router 4
- 构建：Vite
- 测试：Vitest + @vue/test-utils
- 联通方式：
  - 开发环境优先走 Vite Proxy（`frontend/vite.config.ts`）
  - API 基址由 `VITE_API_BASE_URL` 控制（默认为空，走相对路径）

### 后端

- 框架：FastAPI
- 数据层：SQLAlchemy 2.0（async）+ PostgreSQL
- 任务：`jobs` + worker 轮询执行
- 检索/AI：PageIndex + OpenAI（按配置）
- Python 包管理与执行：`uv`

## 3. Phase-1 完成度（对照设计规格）

对照 `docs/specs/2026-03-16-backend-v1-design.md` 的第一阶段核心闭环（1.1）做当前盘点：

| 核心链路 | 状态 | 说明 |
|---|---|---|
| 注册/登录/refresh/登出 | Done | API 与服务、测试链路均存在 |
| 上传后立即可见 processing | Partial | 后端上传与状态具备，前端书库仍以静态数据为主 |
| 解析+建索引+题库预生成 | Done | worker `document_ingestion` 已实现索引与题库生成编排（含失败回写） |
| ready 后进入三模式 | Partial | 前端模式页存在，后端 run 已落地，但前端模式页仍以静态流为主 |
| 完成答题并返回 settlement | Done | runs 服务与仓储已实现，答题完成后可生成 settlement |
| settlement 更新钱包并驱动商店 | Partial | wallet/shop 服务能力有，链路打通不足 |
| 错题解析 + 题目反馈 | Partial | 后端 review/feedback API 有，前端尚未全面接线 |
| 反馈学习沉淀规则库 | Partial | 相关服务/作业有，worker 主流程仍需补齐 |

结论：当前更接近“Phase-1 核心能力基础版（部分链路可用）”，不是“完整闭环已全部打通”。

## 4. 前后端联通现状

### 已完成的联通改造

1. 新增前端 API 基础层：
   - `frontend/src/api/http.ts`
   - `frontend/src/api/system.ts`
2. 新增后端健康检查联通 composable：
   - `frontend/src/composables/useBackendHealth.ts`
3. 首页接入后端健康状态展示：
   - `frontend/src/pages/DungeonScholarHomePage.vue`
4. Vite 代理配置：
   - `frontend/vite.config.ts`
   - 代理 `/api` 与 `/health` 到后端（默认 `http://localhost:8000`）
5. 前端环境变量模板：
   - `frontend/.env.example`

### 说明

- 当前已具备“真实网络联通”的基础能力（前端可请求后端健康接口）。
- 业务接口的端到端联通仍取决于后端各域服务依赖是否已完整接入（当前部分路由仍为占位依赖）。

## 5. 环境准备

## 5.1 通用要求

- Node.js 18+
- Python 3.11+
- `uv`
- PostgreSQL 15+

## 5.2 后端环境变量

复制并编辑：

```bash
cp backend/.env.example backend/.env
```

关键变量（以 `backend/app/core/config.py` 与 `.env.example` 为准）：

| 变量 | 说明 | 默认/示例 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://postgres:postgres@localhost:5432/xirang` |
| `SECRET_KEY` | JWT 签名密钥 | 本地请自定义 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 过期分钟 | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 过期天数 | `7` |
| `OPENAI_API_KEY` | OpenAI Key | 需要时配置 |
| `PAGEINDEX_URL` | PageIndex 地址 | `http://localhost:8080` |
| `PAGEINDEX_API_KEY` | PageIndex 鉴权 | 可空 |
| `STORAGE_MODE` | 存储模式 | `local` |
| `UPLOAD_DIR` | 本地上传目录 | `.data/uploads` |
| `MAX_FILE_SIZE_MB` | 文件大小上限（MB） | `50` |
| `CORS_ORIGINS` | 允许跨域来源（逗号分隔） | `http://localhost:5173,http://localhost:3000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 5.3 前端环境变量

复制并编辑：

```bash
cp frontend/.env.example frontend/.env
```

| 变量 | 说明 | 默认/示例 |
|---|---|---|
| `VITE_API_BASE_URL` | 前端 API 基址。留空时使用相对路径（本地默认通过 Vite `/api` 代理） | 空 |
| `VITE_API_PROXY_TARGET` | Vite 开发代理目标后端地址 | `http://localhost:8000` |
| `VITE_ENABLE_BACKEND_HEALTH_CHECK` | 首页是否自动请求 `/health` 检测后端连通性 | `false` |

## 6. 本地运行

## 6.1 启动后端

```bash
cd backend
uv venv .venv
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

后端健康检查：

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/v1/health`

## 6.2 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：`http://localhost:5173`

## 6.3 联通验证

1. 确保后端在 `8000` 端口运行。
2. 打开前端首页（`/home`）。
3. 观察状态条中的后端连通状态：
   - `Connected to ...` 表示联通成功。
  - `Cannot reach backend service` 表示联通失败，需检查代理或后端是否启动。

如果你看到 Vite 日志：

`[vite] http proxy error: /health AggregateError [ECONNREFUSED]`

通常表示前端代理目标（默认 `http://localhost:8000`）没有可用后端进程。请先启动后端，或把 `VITE_ENABLE_BACKEND_HEALTH_CHECK=false` 保持关闭。

## 7. 质量验证命令

## 7.1 后端（在 `backend/`）

```bash
uv run ruff check app tests
uv run mypy app
uv run pytest tests -q --tb=short
```

## 7.2 前端（在 `frontend/`）

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

## 7.3 启动检查（建议每次联调前执行）

后端（在 `backend/`）：

```bash
uv run pytest tests/api/test_system.py tests/api/test_auth_wiring.py -q --tb=short
```

前端（在 `frontend/`）：

```bash
npm run lint
npm run typecheck
```

## 8. 本次关键修复

1. 清理 FastAPI 422 弃用告警：
   - `backend/app/api/v1/runs.py`
   - `HTTP_422_UNPROCESSABLE_ENTITY` -> `HTTP_422_UNPROCESSABLE_CONTENT`
2. 增加前后端最小联通链路：
   - API client + health 请求 + Vite 代理 + 首页状态展示。
3. 完成 runs 核心闭环实现：
   - 新增 `backend/app/repositories/run_repository.py`
   - 完成 `backend/app/services/runs/service.py` 真实生命周期实现（create/list/submit/settlement）
   - `backend/app/api/v1/runs.py` 接入真实依赖注入
4. 完成 ingestion worker 主流程：
   - `backend/app/workers/main.py` 实现 document ingestion 编排（文档读取、索引、题库生成、状态回写）
   - 扩展 `backend/app/repositories/document_repository.py` 以支持 ingestion/question-set 持久化
5. 贯通 settlement -> wallet/shop：
   - `backend/app/services/runs/service.py` 在 run 结算时自动写入 COIN 与 XP 账本（幂等 key）
   - 新增 `backend/app/repositories/wallet_repository.py` 与 `backend/app/repositories/shop_repository.py`
   - `backend/app/api/v1/shop.py` 实装 `/items` `/purchase` `/inventory` `/balance` `/ledger`

## 9. 常见问题

### Q1: 前端显示后端离线

- 检查后端是否启动在 `http://localhost:8000`
- 检查 `frontend/.env` 中 `VITE_API_PROXY_TARGET`
- 检查后端 `CORS_ORIGINS` 是否包含前端地址

### Q2: 本地测试通过但业务接口返回 500

- 部分 API 在当前阶段仍依赖占位实现或未完成接线。
- 测试中很多接口使用 dependency override/fake service，不等价于生产 wiring 全量完工。

### Q4: 如何快速判断 auth 链路是否异常

- 检查后端日志中的 `auth_request` 事件：
  - 成功样例：`auth_request endpoint=/api/v1/auth/login status_code=200 ...`
  - 告警样例：`auth_request endpoint=/api/v1/auth/register status_code=409 ... failure_reason=duplicate_identity`
- 如果出现 5xx，请优先检查：
  - `backend/app/api/v1/auth.py` 的 `get_auth_service` 是否是可执行依赖注入
  - `backend/app/repositories/auth_repository.py` 是否存在真实实现

### Q3: 为什么只接了健康检查

- 当前目标是先确保前后端网络与配置层联通可观测。
- 完整业务闭环仍需继续补齐 runs/ingestion/shop 等核心链路实现。

## 10. 下一步建议

按 Phase-1 核心闭环优先级，建议继续：

1. 完成 `runs` 服务真实实现（创建 run、答题、settlement）。
2. 完成 worker ingestion 主流程（解析、索引、题库预生成）。
3. 暴露 shop/wallet 的完整 API，并将前端从静态数据切换到真实调用。
