# 外部服务集成模板

用于接入 R2、Resend、Creem、PageIndex、MinerU、OAuth provider 或其他外部服务。目标是避免“代码已接入、部署变量或验证遗漏”。

## 1. 配置层

- [ ] 在 `backend/app/core/config.py` 增加 typed settings。
- [ ] 在 `backend/.env.example` 增加空占位或安全默认值。
- [ ] 在 `docs/env-matrix.md` 增加变量归属、是否 secret、API/Worker/Vercel 使用范围。
- [ ] 在 Render API Dashboard 添加生产变量。
- [ ] 如 Worker 需要访问，同步添加到 Render Worker Dashboard。
- [ ] 如前端需要公开配置，添加到 Vercel Dashboard，且只使用 `VITE_` 公共变量。
- [ ] 不读取、打印或提交真实 secret。

## 2. Client 层

- [ ] 新增 `backend/app/integrations/<service>/client.py`。
- [ ] 明确 base URL、timeout、headers、认证方式和 test/prod 环境切换。
- [ ] 明确 retry/backoff 策略、可重试错误范围、最大重试次数和不可重试错误。
- [ ] 将第三方错误映射为项目内部异常或 typed result。
- [ ] 日志只记录状态码、错误类型和 request id，不记录 secret 或敏感 payload。
- [ ] 提供 fake client、stub transport 或 mock fixture，避免单测访问真实外部服务。

## 3. Service 层

- [ ] 新增或扩展 `backend/app/services/<domain>/`。
- [ ] 将业务规则放在 service，不放在 API handler。
- [ ] 明确配置缺失、外部超时、认证失败、限流、不可用的降级策略。
- [ ] 如有 mock fallback，明确只适用于本地/测试还是生产可降级。

## 4. API / Schema 层

- [ ] 在 `backend/app/api/v1/` 暴露必要端点。
- [ ] 在 `backend/app/schemas/` 定义请求/响应 schema。
- [ ] API 层只做认证、依赖注入、HTTP 错误映射。
- [ ] 明确 400/401/403/409/422/429/503 等错误语义。
- [ ] 涉及 webhook 时必须实现签名校验和幂等处理。

## 5. 测试层

- [ ] Client 单测覆盖认证 header、base URL、timeout、错误响应。
- [ ] Service 单测覆盖业务成功、配置缺失、外部失败、降级策略。
- [ ] API 测试覆盖认证、schema、错误码和依赖 override。
- [ ] 配置测试覆盖 `.env.example` 变量与 Settings 字段一致性。
- [ ] Webhook 测试覆盖签名失败、重复事件、成功处理。

## 6. 部署层

- [ ] 更新 `docs/deployment-checklist.md` 的外部服务检查项。
- [ ] 更新 `docs/smoke-checklist.md` 的发布后验证项。
- [ ] 更新 `docs/render-blueprint-template.md` 中 API/Worker 变量分类。
- [ ] 如果服务涉及用户输入、认证、支付、webhook 或 secret，触发 security review。

## 7. 验收

- [ ] 本地测试通过。
- [ ] 生产 Dashboard 变量已填充。
- [ ] 发布后 smoke 验证通过。
- [ ] 如 smoke 失败，记录到 `docs/friction-log.md` 并补充可复用规则。
