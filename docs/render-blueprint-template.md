# Render Blueprint 替代模板

真实 `render.yaml` 不作为常规跟踪文件提交。Render Dashboard 是运行时事实来源，本模板是可审阅、可重建的配置清单。任何 Dashboard 配置变更都应同步更新本文件和 `docs/env-matrix.md`。

## 不跟踪策略

- 不提交真实 `render.yaml`、`render.yml`、`render.ymal`。
- 不在文档中写真实 secret、token、API key、webhook secret 或数据库密码。
- 变量名、用途、是否 secret、平台归属写在 `docs/env-matrix.md`。
- 本文件记录服务结构、命令、health path 和变量分类。

## API Web Service

| 配置项 | 建议值 |
|---|---|
| Service type | Web Service |
| Name | `xirang-api` |
| Runtime | Python |
| Root directory | `backend` |
| Region | 与主要用户和数据库区域尽量接近 |
| Branch | 当前生产分支 |
| Build command | `pip install uv && uv sync --frozen --no-dev && uv cache prune` |
| Start command | `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |

### API 环境变量分类

| 分类 | 变量 |
|---|---|
| 基础 | `APP_ENV`、`LOG_LEVEL`、`BACKEND_BASE_URL`、`FRONTEND_BASE_URL`、`CORS_ORIGINS` |
| 数据库与安全 | `DATABASE_URL`、`SECRET_KEY`、`ACCESS_TOKEN_EXPIRE_MINUTES`、`REFRESH_TOKEN_EXPIRE_DAYS` |
| 存储 | `STORAGE_MODE`、`UPLOAD_DIR`、`MAX_FILE_SIZE_MB`、R2 系列变量 |
| LLM/OCR/索引 | NVIDIA、OpenAI、PageIndex、MinerU 系列变量 |
| OAuth | GitHub、Google、Microsoft client/callback 系列变量 |
| 邮件验证码 | Resend 与验证码策略变量 |
| 支付 | Creem API、webhook、product、定价区域变量 |

## Background Worker

| 配置项 | 建议值 |
|---|---|
| Service type | Background Worker |
| Name | `xirang-worker` |
| Runtime | Python |
| Root directory | `backend` |
| Region | 与 API 和数据库区域尽量一致 |
| Branch | 当前生产分支 |
| Build command | `pip install uv && uv sync --frozen --no-dev && uv cache prune` |
| Start command | `uv run python -m app.workers.main` |

### Worker 环境变量分类

| 分类 | 变量 |
|---|---|
| 必须与 API 一致 | `APP_ENV`、`DATABASE_URL`、`SECRET_KEY`、`STORAGE_MODE`、R2 系列变量、LLM provider 变量 |
| Worker-only | `WORKER_POLL_INTERVAL_SECONDS`、`WORKER_MAX_CONCURRENT_JOBS` |
| 文档处理依赖 | `PAGEINDEX_URL`、`PAGEINDEX_MOCK_FALLBACK`、`MINERU_URL`、`MINERU_TIMEOUT_SECONDS`、`MINERU_BACKEND`、`MINERU_LANG_LIST` |
| 不建议继承 | OAuth callback、CORS、Creem checkout、Resend 发信变量，除非 Worker 代码确实需要 |

## Dashboard 改动同步规则

- 新增环境变量：同步更新 `backend/.env.example`、`docs/env-matrix.md` 和本模板。
- 修改服务命令：同步更新本模板和 `docs/deployment-checklist.md`。
- 修改前端/API 域名：同步更新 Vercel rewrite、Render `BACKEND_BASE_URL`、`FRONTEND_BASE_URL`、OAuth callback、Creem success/cancel URL。
- 修改外部服务地址：同步更新 env matrix，并在 `docs/smoke-checklist.md` 增加验证项。
- smoke 失败：记录到 `docs/friction-log.md`。

## Review 清单

- [ ] 没有真实 secret 写入文档。
- [ ] API 与 Worker 的数据库、存储、LLM/OCR 变量一致性已核对。
- [ ] API health check path 与实际 `/health` 一致。
- [ ] Worker 不被当作 HTTP web service 检查。
- [ ] Dashboard 改动已同步到 env matrix 和 smoke checklist。
