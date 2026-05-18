# 优化规格文档

**日期**: 2026-05-15
**基于报告**: `docs/insights/2026-05-15-insights.md`
**优化范围**: 部署链路清单、环境变量一致性、Render 配置替代清单、外部服务集成模板、发布后 smoke 验证

## 优先级矩阵

| 优先级 | 优化项 | 影响 | 成本 | 选择 |
|---|---|---:|---:|---|
| P0 | 建立 Vercel + Render 部署链路清单 | 10 | 2 | 本次 |
| P0 | 建立 Render/Vercel 环境变量一致性检查 | 10 | 3 | 本次 |
| P0 | `render.yaml` 不跟踪后的替代部署清单 | 9 | 2 | 本次 |
| P1 | 创建外部服务集成模板 | 8 | 3 | 本次 |
| P1 | 发布后 smoke 验证清单/脚本化入口 | 9 | 3 | 本次 |

## 优化项 1: Vercel + Render 部署链路清单 [P0]

### 问题

近期部署摩擦集中在 Vercel rewrite、前端 API base、Render `CORS_ORIGINS`、`FRONTEND_BASE_URL`、OAuth callback、Vercel 静态资源缓存，以及 PageIndex worker/web service 健康检查语义混淆。

### 方案

新增 `docs/deployment-checklist.md`，覆盖：

- Vercel：rewrite 目标域名、`VITE_API_BASE_URL` 策略、SPA fallback、无缓存 redeploy。
- Render Web Service：`CORS_ORIGINS`、`FRONTEND_BASE_URL`、API 域名、health check path。
- Render Worker：worker 是否需要部署、容器内外部服务可达性、worker 健康状态语义。
- OAuth Provider：GitHub/Google/Microsoft callback URL 与 API 域名一致性。

### 验证

- 文档包含 Vercel、Render API、Render Worker、OAuth、缓存五类清单。
- 任意部署变更前可按清单逐项核对。

## 优化项 2: Render/Vercel 环境变量一致性检查 [P0]

### 问题

环境变量来源分散在 `.env.example`、Render Dashboard、Vercel Dashboard、`frontend/vercel.json` 和历史 `render.yaml` 中。新增 R2、Resend、Creem、PageIndex、MinerU 后，遗漏风险上升。

### 方案

新增 `docs/env-matrix.md`，按平台维护变量矩阵：

- 前端 Vercel：`VITE_API_BASE_URL`、`VITE_ENABLE_BACKEND_HEALTH_CHECK`、`VITE_APP_BASE_URL`。
- 后端 Render API：`APP_ENV`、`DATABASE_URL`、`SECRET_KEY`、`CORS_ORIGINS`、`FRONTEND_BASE_URL`、R2、OAuth、Resend、Creem、PageIndex/MinerU。
- Render Worker：标注 API 与 Worker 必须一致、只属于 Worker、以及不应继承的 Web-only 变量。

一致性规则：

- `CORS_ORIGINS` 必须包含当前 Vercel 域名。
- `FRONTEND_BASE_URL` 必须等于主要前端域名。
- OAuth callback URL 必须使用 API 域名。
- `frontend/vercel.json` rewrite destination 必须使用同一 API 域名。
- API 与 Worker 的 `DATABASE_URL`、`STORAGE_MODE`、R2、LLM provider 变量应一致。
- `PAGEINDEX_URL` 必须明确区分 mock、本地、外部 web service、worker 四种语义。

### 验证

- `docs/env-matrix.md` 存在。
- 每个新增外部服务必须在矩阵中有条目。

## 优化项 3: `render.yaml` 替代部署清单 [P0]

### 问题

`render.yaml` 已从 Git 跟踪中移除并加入 `.gitignore`。如果没有替代清单，Render Dashboard 配置会变成不可 review 的隐式状态。

### 方案

新增 `docs/render-blueprint-template.md`，记录：

- Render API 服务模板：service name、rootDir、buildCommand、startCommand、healthCheckPath、envVars 分类。
- Render Worker 服务模板：service name、rootDir、buildCommand、startCommand、worker envVars 分类。
- 不跟踪策略：仓库不提交真实 `render.yaml`，secret 只保存在 Render Dashboard。
- Dashboard 改动同步规则：必须同步更新 `docs/env-matrix.md` 与 `docs/render-blueprint-template.md`。

### 验证

- 即使不提交真实 `render.yaml`，仍可根据模板重建 API + Worker。
- 任一新增 env var 能在 `.env.example`、env matrix、Render template 三处找到对应说明。

## 优化项 4: 外部服务集成模板 [P1]

### 问题

R2、Resend、Creem、PageIndex/OCR、MinerU、OAuth 等集成都涉及 config、client、service、schema、API、测试、env、部署配置。缺少模板会造成遗漏。

### 方案

新增 `docs/templates/external-service-integration-template.md`，覆盖：

- 配置层：`backend/app/core/config.py`、`backend/.env.example`、Render API env、Render Worker env、Vercel env。
- Client 层：`backend/app/integrations/<service>/`、timeout、retry、error mapping、test double。
- Service 层：业务异常、降级策略、mock fallback。
- API 层：schema、权限、错误码。
- 测试层：client、service、API、配置缺失测试。
- 部署层：env matrix 条目、smoke 验证项、security-review 触发条件。

### 验证

- 新增模板文档存在。
- 下一个外部服务集成可以直接按模板生成设计与计划。

## 优化项 5: 发布后 smoke 验证清单 [P1]

### 问题

部分问题不会被业务单测覆盖，只会在部署后暴露，例如 rewrite、CORS、OAuth callback、chunk 404、worker 外部依赖不可达。

### 方案

新增 `docs/smoke-checklist.md`，先文档化，后续再脚本化：

- 前端静态资源：打开首页和 `/login`，刷新路由不 404，Network 无 chunk 404。
- API 连通性：`GET /health`、`GET /api/v1/health`、`GET /api/v1/health/ready`。
- 登录链路：邮箱登录/注册、OAuth 跳转、callback URL。
- 外部服务：R2、Resend、Creem、PageIndex、MinerU。
- Worker：日志无启动错误，ingestion job 状态推进，外部依赖不可用时错误语义清晰。

### 验证

- `docs/smoke-checklist.md` 存在。
- 每次部署后按 smoke 清单记录通过/失败。
- smoke 失败时补充 `docs/friction-log.md`。

## 风险与缓解

- 风险：文档增加但执行纪律不足。
- 缓解：每个外部服务集成必须更新 env matrix；每次部署变更必须更新部署清单；每次 smoke 失败必须写入 friction-log。
- 回滚：本优化仅新增/更新文档和清单，不改变运行时代码。

## 建议创建/修改文件

- 新增: `docs/deployment-checklist.md`
- 新增: `docs/env-matrix.md`
- 新增: `docs/render-blueprint-template.md`
- 新增: `docs/templates/external-service-integration-template.md`
- 新增: `docs/smoke-checklist.md`
- 修改: `docs/deployment-guide.md`
- 修改: `docs/friction-log.md`

## 下一步

1. 审批本优化规格。
2. 运行 `/plan`，拆分为 2-5 分钟粒度实施任务。
3. 优先交付部署链路清单、env matrix、Render blueprint template、smoke checklist。
