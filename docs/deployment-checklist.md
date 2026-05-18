# 部署链路检查清单

本清单用于任何 Vercel、Render、OAuth、环境变量、外部服务或域名变更前后核对。真实 secret 不写入仓库，只在平台 Dashboard 中维护。

## 部署前

- [ ] 确认本次变更是否影响前端域名、API 域名、OAuth callback、CORS、环境变量或外部服务。
- [ ] 对照 `docs/env-matrix.md` 核对 Vercel、Render API、Render Worker 的变量归属。
- [ ] 对照 `docs/render-blueprint-template.md` 核对 Render Dashboard 中 API 和 Worker 配置。
- [ ] 确认 `render.yaml`、`render.yml`、`render.ymal` 不作为常规跟踪文件提交。
- [ ] 确认 `.env`、`.env.local`、平台 secret、API key、webhook secret 没有进入暂存区。

## Vercel

- [ ] `frontend/vercel.json` 的 `/api/(.*)` rewrite 指向当前 Render API 域名，并保留 `/api/$1` 后缀。
- [ ] `frontend/vercel.json` 的 `/health` rewrite 指向当前 Render API 的 `/health`。
- [ ] `frontend/vercel.json` 保留 SPA fallback：`/(.*)` -> `/index.html`。
- [ ] 使用 Vercel rewrite 时，`VITE_API_BASE_URL` 为空；若显式配置 API base，确认不会重复拼接 `/api/v1`。
- [ ] `VITE_ENABLE_BACKEND_HEALTH_CHECK` 的生产值与登录页健康检查策略一致。
- [ ] 自定义域名变更后，`VITE_APP_BASE_URL` 与主前端域名一致。
- [ ] 线上出现 chunk 404、动态 import 失败或旧页面资源时，执行无缓存 redeploy。

## Render API

- [ ] API 服务 root directory 为 `backend`。
- [ ] build command 使用 uv 安装并同步依赖。
- [ ] start command 先执行 Alembic 迁移，再启动 uvicorn。
- [ ] health check path 为 `/health`，且浏览器访问返回 `status=ok`。
- [ ] `CORS_ORIGINS` 包含当前 Vercel 主域名。
- [ ] `FRONTEND_BASE_URL` 等于当前 Vercel 主域名。
- [ ] `BACKEND_BASE_URL` 等于当前 API 域名。
- [ ] `DATABASE_URL` 指向当前 Supabase PostgreSQL，并与 Worker 一致。
- [ ] `SECRET_KEY`、OAuth secret、R2 secret、Resend API key、Creem API key、webhook secret 仅在 Render Dashboard 中维护。

## Render Worker

- [ ] 明确本次是否需要部署 Worker；如果暂停文档处理，可以只部署 API。
- [ ] Worker root directory 为 `backend`。
- [ ] Worker start command 为 `uv run python -m app.workers.main` 或等价命令。
- [ ] Worker 与 API 使用同一 `DATABASE_URL`、`STORAGE_MODE`、R2 配置和 LLM provider 配置。
- [ ] Worker 的 `PAGEINDEX_URL` 指向容器内可达的真实 PageIndex 服务，不把浏览器可达误认为容器内可达。
- [ ] Worker 的 MinerU 配置与实际可达服务一致；不可用时明确非文本文件会失败或降级。
- [ ] Worker 日志无启动错误，job 能从 pending 推进到 processing/ready 或明确失败原因。

## OAuth Provider

- [ ] GitHub callback URL 指向当前 API 域名：`/api/v1/auth/oauth/github/callback`。
- [ ] Google callback URL 指向当前 API 域名：`/api/v1/auth/oauth/google/callback`。
- [ ] Microsoft callback URL 指向当前 API 域名：`/api/v1/auth/oauth/microsoft/callback`。
- [ ] Render 中 `GITHUB_CALLBACK_URL`、`GOOGLE_CALLBACK_URL`、`MICROSOFT_CALLBACK_URL` 与 Provider Dashboard 完全一致。

## 外部服务

- [ ] 新增或修改外部服务前，先使用 `docs/templates/external-service-integration-template.md` 检查配置、client、service、API、测试和部署项。
- [ ] R2 bucket/account/access key/public URL 配置完整，API 与 Worker 一致。
- [ ] Resend `RESEND_API_KEY`、`RESEND_FROM_EMAIL` 已配置；`RESEND_FROM_EMAIL` 使用已验证的 `@xiranglearn.quest` 发件人，验证码 TTL、冷却和尝试次数符合设计。
- [ ] Creem API key、webhook secret、product id、success/cancel URL 已配置；测试 key 使用测试环境。
- [ ] PageIndex ready/disconnected 排查时区分 mock fallback、本地服务、外部 web service、worker 四种语义。
- [ ] MinerU URL、timeout、backend、language 与实际部署一致。

## 部署后

- [ ] 按 `docs/smoke-checklist.md` 完成发布后 smoke 验证。
- [ ] smoke 失败时补充 `docs/friction-log.md`，并标记是否需要更新 env matrix、deployment checklist 或 Render template。
- [ ] 若 Dashboard 中变更了环境变量或服务命令，同步更新 `docs/env-matrix.md` 和 `docs/render-blueprint-template.md`。
