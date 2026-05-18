# Friction Log

> 记录开发中的摩擦事件（代码与非代码），用于 `/insights` 和 `/optimize` 分析。

## 模板
- 日期: YYYY-MM-DD
- 场景: （如 登录流程 / 部署配置 / 路由跳转）
- 关联清单/Smoke 项: （如 docs/smoke-checklist.md#api-连通性）
- 现象: （发生了什么）
- 根因: （已确认原因）
- 处理: （采取的修复动作）
- 耗时: （分钟）
- 是否需要更新 env matrix: 是/否
- 是否需要更新 deployment checklist: 是/否
- 是否需要更新 render template: 是/否
- 是否可复用为规则: 是/否

发布后 smoke 每次执行都应记录结果摘要；失败必须记录完整事件。如果根因涉及 Vercel、Render、OAuth、环境变量或外部服务配置，还需要同步检查 `docs/env-matrix.md`、`docs/deployment-checklist.md` 和 `docs/render-blueprint-template.md`。

---

## 2026-05-14 — 登录失败与环境链路摩擦
- 日期: 2026-05-14
- 场景: Vercel 前端 + Render 后端登录链路
- 现象: 本地与线上出现登录失败；修复后又出现动态 import chunk 加载失败
- 根因: 1) 前端 API 基址与请求路径存在重复 `/api/v1` 风险；2) Render 环境变量仍指向旧域名；3) Vercel 部署缓存导致 `index.html` 与 assets chunk 版本不一致；4) PageIndex 使用 worker 形态与健康检查预期的 HTTP 服务模型不一致
- 处理: 1) 修复 `resolveUrl` 去重逻辑并补充单测；2) 统一 Vercel rewrite 与 Render 域名/OAuth 回调配置；3) 无缓存 Redeploy；4) 调整 `PAGEINDEX_URL` 到可连通路径并复测 ready 健康状态
- 耗时: 150
- 是否可复用为规则: 是

## 2026-05-14 — PageIndex ready/disconnected 误判摩擦
- 日期: 2026-05-14
- 场景: `/api/v1/health/ready` pageindex 状态排障
- 现象: 浏览器访问 `/pageindex/health` 显示 `ok`，但 ready 接口持续 `pageindex=disconnected`
- 根因: 外部访问通不等于后端容器内可达；且 worker 不直接提供标准 HTTP 健康链路
- 处理: 明确区分 mock fallback、worker、web service 语义；重新校验 `PAGEINDEX_URL` 生效值并重启服务，最终达到 `status=ready`
- 耗时: 45
- 是否可复用为规则: 是
