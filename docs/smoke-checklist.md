# 发布后 Smoke 验证清单

每次 Vercel、Render、环境变量、OAuth、外部服务或域名变更后执行。每次 smoke 执行后记录结果摘要；失败项必须记录到 `docs/friction-log.md`，并判断是否需要更新 `docs/env-matrix.md`、`docs/deployment-checklist.md` 或 `docs/render-blueprint-template.md`。

## 执行记录

- 日期:
- 版本/提交:
- 验证人:
- 结果: 通过/失败
- 结果摘要:
- 失败项: 无或列出清单项

## 前端静态资源

- [ ] 打开 Vercel 首页，页面正常渲染。
- [ ] 打开 `/login`，页面正常渲染。
- [ ] 直接刷新 `/login` 或其他 Vue Router 路由不返回 404。
- [ ] DevTools Network 无 JS/CSS chunk 404。
- [ ] 如出现动态 import 失败，执行无缓存 redeploy 并复测。

## API 连通性

- [ ] `GET /health` 返回 `status=ok` 或等价健康状态。
- [ ] `GET /api/v1/health` 能通过 Vercel rewrite 到达后端。
- [ ] `GET /api/v1/health/ready` 返回可解释的依赖状态。
- [ ] 浏览器请求无 CORS 错误。
- [ ] Render API logs 无启动循环或迁移失败。

## 认证链路

- [ ] 邮箱注册验证码可以发送。
- [ ] 邮箱注册提交验证码后可以创建账号并登录。
- [ ] 邮箱/密码登录成功。
- [ ] GitHub OAuth 可以跳转到 Provider。
- [ ] Google OAuth 可以跳转到 Provider。
- [ ] Microsoft OAuth 可以跳转到 Provider。
- [ ] OAuth callback URL 使用当前 API 域名，不指向旧 Render 域名。

## 外部服务

- [ ] R2 上传和读取路径可用，公开 URL 策略符合预期。
- [ ] Resend 发信成功；失败时 API 返回清晰错误，不创建未验证账号。
- [ ] Creem checkout 能创建并跳转到测试/生产环境对应 checkout URL。
- [ ] Creem webhook 端点可达，签名 secret 与 Dashboard 一致。
- [ ] PageIndex ready 状态可解释；区分浏览器可达和容器内可达。
- [ ] MinerU health 可达；PDF/OCR 流程可用或错误语义清晰。

## Worker

- [ ] Worker logs 无启动错误。
- [ ] `document_ingestion` job 能从 pending 进入 processing。
- [ ] 成功路径下 job/doc 状态最终进入 ready。
- [ ] PageIndex 不可用时错误信息明确，不误判为 API 挂掉。
- [ ] MinerU 不可用时非文本文件失败原因明确。
- [ ] Worker 与 API 使用同一数据库、存储和 LLM/OCR 配置。

## 失败记录模板

```markdown
## YYYY-MM-DD — Smoke 失败标题
- 日期: YYYY-MM-DD
- 场景: 发布后 smoke / 部署配置 / 外部服务
- 关联清单/Smoke 项: docs/smoke-checklist.md#...
- 现象:
- 根因:
- 处理:
- 耗时:
- 是否需要更新 env matrix: 是/否
- 是否需要更新 deployment checklist: 是/否
- 是否需要更新 render template: 是/否
- 是否可复用为规则: 是/否
```
