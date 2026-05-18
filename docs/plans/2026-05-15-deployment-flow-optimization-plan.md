# 部署流程优化实施计划

## 总览

本计划将 `docs/optimizations/2026-05-15-deployment-flow-optimization.md` 拆解为文档型实施任务，不改动运行时代码。核心交付物是部署链路清单、环境变量矩阵、Render 替代配置模板、外部服务集成模板、发布后 smoke 清单，并把它们与现有 `docs/deployment-guide.md` 和 `docs/friction-log.md` 串联起来。

本次计划需覆盖最新设计文档中新增/即将新增的外部服务变量：Resend、Creem，以及已有 R2、OAuth、PageIndex、MinerU 等部署风险点。

## 前置准备

- [x] 确认优化规格 `docs/optimizations/2026-05-15-deployment-flow-optimization.md` 已批准。
- [x] 确认已读取最新设计文档：`docs/designs/2026-05-15-email-verification-registration-design.md`、`docs/designs/2026-05-15-creem-payment-integration-design.md`。
- [x] 确认 `docs/plans/` 目录存在。
- [x] 确认本次仅新增/修改文档，不修改业务代码。
- [x] 注意不要读取或提交真实 `.env` secret 内容。

## 任务列表

### 任务 1: 梳理部署文档现状 (~3 min) [完成]

- **描述**: 对照优化规格，确认现有 `docs/deployment-guide.md` 中与 Vercel、Render、OAuth、Worker、PageIndex、MinerU 相关内容，标记后续需要引用或替换的段落。
- **文件**: `docs/deployment-guide.md`、`docs/friction-log.md`、`frontend/vercel.json`
- **测试**: 无代码测试。
- **验证**: 明确新增文档不会与 `deployment-guide.md` 冲突；明确 `render.yaml` 不应作为唯一部署事实来源。
- **依赖**: 无

### 任务 2: 创建部署链路清单 (~4 min) [完成]

- **描述**: 新增部署前/部署变更检查清单，覆盖 Vercel、Render API、Render Worker、OAuth、缓存五类风险。
- **文件**: 创建 `docs/deployment-checklist.md`
- **测试**: 无代码测试。
- **验证**: 文档包含 Vercel rewrite、`VITE_API_BASE_URL`、SPA fallback、无缓存 redeploy；包含 Render API 的 `CORS_ORIGINS`、`FRONTEND_BASE_URL`、API 域名、health check path；包含 Worker 部署必要性、外部服务可达性、健康状态语义；包含 OAuth callback URL 与 API 域名一致性检查。
- **依赖**: 任务 1

### 任务 3: 创建环境变量矩阵骨架 (~3 min) [完成]

- **描述**: 新增环境变量矩阵文档，先建立平台分区和一致性规则结构。
- **文件**: 创建 `docs/env-matrix.md`
- **测试**: 无代码测试。
- **验证**: 文档包含 Vercel、Render API、Render Worker 三个平台区块；包含一致性规则区块；明确“不记录真实 secret 值，只记录变量名、用途、来源和一致性要求”。
- **依赖**: 任务 1

### 任务 4: 填充核心部署变量矩阵 (~5 min) [完成]

- **描述**: 在环境变量矩阵中填入核心变量与跨平台一致性规则。
- **文件**: 修改 `docs/env-matrix.md`
- **测试**: 无代码测试。
- **验证**: Vercel 区块包含 `VITE_API_BASE_URL`、`VITE_ENABLE_BACKEND_HEALTH_CHECK`、`VITE_APP_BASE_URL`；Render API 区块包含 `APP_ENV`、`DATABASE_URL`、`SECRET_KEY`、`CORS_ORIGINS`、`FRONTEND_BASE_URL`；Render Worker 区块标注与 API 必须一致的变量、Worker-only 变量、Web-only 变量；一致性规则覆盖 `CORS_ORIGINS`、`FRONTEND_BASE_URL`、OAuth callback、`frontend/vercel.json` rewrite。
- **依赖**: 任务 3

### 任务 5: 补充外部服务变量矩阵 (~5 min) [完成]

- **描述**: 根据现有部署指南和最新设计文档，把外部服务变量补充到环境变量矩阵。
- **文件**: 修改 `docs/env-matrix.md`
- **测试**: 无代码测试。
- **验证**: 矩阵包含 R2/storage、OAuth、Resend、Creem、PageIndex/MinerU 变量，并明确 `PAGEINDEX_URL` 的 mock、本地、外部 web service、worker 语义区别。
- **依赖**: 任务 4

### 任务 6: 创建 Render API Blueprint 替代模板 (~4 min) [完成]

- **描述**: 新增 Render 配置模板文档，先记录 API Web Service 的可重建配置。
- **文件**: 创建 `docs/render-blueprint-template.md`
- **测试**: 无代码测试。
- **验证**: 文档包含 API service name、rootDir、buildCommand、startCommand、healthCheckPath；包含 API env vars 分类；明确真实 secret 只放 Render Dashboard，不提交仓库。
- **依赖**: 任务 1、任务 5

### 任务 7: 补充 Render Worker 模板与同步规则 (~4 min) [完成]

- **描述**: 在 Render 模板中补充 Worker 配置和 Dashboard 改动同步规则。
- **文件**: 修改 `docs/render-blueprint-template.md`
- **测试**: 无代码测试。
- **验证**: 文档包含 Worker service name、rootDir、buildCommand、startCommand；标注 Worker 依赖 PageIndex、MinerU、数据库、存储等变量；明确 `render.yaml` 不作为跟踪文件时，必须同步更新 `docs/env-matrix.md` 与 `docs/render-blueprint-template.md`。
- **依赖**: 任务 6

### 任务 8: 创建外部服务集成模板目录与模板 (~5 min) [完成]

- **描述**: 新增外部服务集成模板，供 Resend、Creem、R2、PageIndex、MinerU、OAuth 等后续集成复用。
- **文件**: 创建 `docs/templates/external-service-integration-template.md`
- **测试**: 无代码测试。
- **验证**: 模板包含配置层、Client 层、Service 层、API 层、测试层、部署层；明确需要更新 `backend/app/core/config.py`、`backend/.env.example`、Render API env、Render Worker env、Vercel env；包含 timeout、retry、error mapping、test double、配置缺失测试、security-review 触发条件。
- **依赖**: 任务 5

### 任务 9: 创建发布后 smoke 验证清单 (~5 min) [完成]

- **描述**: 新增部署后 smoke checklist，覆盖静态资源、API、认证、外部服务、Worker。
- **文件**: 创建 `docs/smoke-checklist.md`
- **测试**: 无代码测试。
- **验证**: 文档包含首页和 `/login` 刷新不 404、Network 无 chunk 404；包含 `/health`、`/api/v1/health`、`/api/v1/health/ready`；包含邮箱登录/注册、OAuth 跳转和 callback URL；包含 R2、Resend、Creem、PageIndex、MinerU；包含 Worker 日志、job 状态推进、外部依赖不可用时错误语义；要求 smoke 失败时补充 `docs/friction-log.md`。
- **依赖**: 任务 5

### 任务 10: 更新部署指南入口与过时说明 (~5 min) [完成]

- **描述**: 修改现有部署指南，把新增清单作为部署入口，并避免继续把真实 `render.yaml` 作为唯一 source of truth。
- **文件**: 修改 `docs/deployment-guide.md`
- **测试**: 无代码测试。
- **验证**: 文档开头或部署检查清单章节链接到 `docs/deployment-checklist.md`、`docs/env-matrix.md`、`docs/render-blueprint-template.md`、`docs/smoke-checklist.md`；原有“提交 `render.yaml`”相关内容补充说明：如真实 Blueprint 不跟踪，则以 Render Dashboard + 模板文档为准；部署变更前后均有明确检查入口。
- **依赖**: 任务 2、任务 5、任务 7、任务 9

### 任务 11: 更新摩擦日志模板 (~3 min) [完成]

- **描述**: 强化 `friction-log` 对部署和 smoke 失败的记录格式。
- **文件**: 修改 `docs/friction-log.md`
- **测试**: 无代码测试。
- **验证**: 模板增加“关联清单/Smoke 项”字段；增加“是否需要更新 env matrix / deployment checklist / render template”字段；明确 smoke 失败必须记录。
- **依赖**: 任务 9

### 任务 12: 文档交叉引用完整性检查 (~4 min) [完成]

- **描述**: 检查新增文档之间的链接和命名一致性，避免孤立文档。
- **文件**: `docs/deployment-checklist.md`、`docs/env-matrix.md`、`docs/render-blueprint-template.md`、`docs/templates/external-service-integration-template.md`、`docs/smoke-checklist.md`、`docs/deployment-guide.md`、`docs/friction-log.md`
- **测试**: 无代码测试。
- **验证**: 每个新增文档至少被 `docs/deployment-guide.md` 或相关文档引用一次；外部服务模板引用 env matrix 和 smoke checklist；env matrix 引用 Render template；smoke checklist 引用 friction log。
- **依赖**: 任务 10、任务 11

### 任务 13: 最终验收检查 (~3 min) [完成]

- **描述**: 对照优化规格逐项验收。
- **文件**: 检查所有新增/修改文档。
- **测试**: 文档型变更无需运行前后端测试；建议运行 `git diff -- docs` 人工审阅文档差异。
- **验证**: 优化规格第 1-5 项均有对应交付物；无真实 secret、token、API key 被写入文档；文档明确 Render/Vercel/Worker/OAuth/PageIndex/MinerU/Resend/Creem 的部署检查点。
- **依赖**: 任务 12

## 并行机会

- 任务 2、任务 3、任务 6、任务 9 可在任务 1 后并行起草。
- 任务 5 和任务 8 可并行，但最终需要互相校对变量命名。
- 任务 10 和任务 11 可在所有新增文档完成后并行执行。
- 任务 13 必须最后执行。

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|---|---:|---:|---|
| 文档新增但没人执行 | 中 | 高 | 在 `deployment-guide.md` 中把新增清单设为部署入口 |
| env matrix 与真实 Dashboard 漂移 | 中 | 高 | 要求 Dashboard 变更必须同步更新 env matrix 与 Render template |
| 写入真实 secret | 低 | 高 | 文档只写变量名、用途、来源，不写真实值 |
| `render.yaml` 状态与文档表述冲突 | 中 | 中 | 文档明确“不跟踪真实 Blueprint 时”的替代 source of truth |
| 外部服务变量遗漏 | 中 | 中 | 使用最新设计文档校对 Resend、Creem，并覆盖 R2、OAuth、PageIndex、MinerU |

## 测试策略

| 层级 | 内容 | 覆盖目标 |
|---|---|---|
| 文档存在性 | 检查 5 个新增文档存在 | 优化规格交付物完整 |
| 文档一致性 | 检查 deployment guide、env matrix、render template、smoke checklist 互相引用 | 避免孤立清单 |
| 安全检查 | 检查文档不包含真实 secret/token/API key | 防止敏感信息泄漏 |
| 部署流程检查 | 使用 checklist 模拟一次部署变更核对 | 确认可执行 |
| Smoke 流程检查 | 使用 smoke checklist 模拟一次发布后验证 | 确认可记录失败并回写 friction log |
