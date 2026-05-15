# Creem 支付集成实施计划

## 总览
基于设计文档实现 Creem 支付闭环：后端提供 Checkout、Webhook、订阅管理、地区定价 API；前端在价格页/商城页/设置页接入支付与地区切换。
采用“后端先落地 contract + webhook 幂等更新，再接前端交互”的策略，确保支付成功后代币与订阅状态可稳定回写。
关键决策：以 `users` 扩展字段作为订阅真值来源；Webhook 作为最终一致性入口；地区默认 `standard`，手动切换可覆盖自动检测。

## 前置准备
- [ ] 确认设计文档已批准：`docs/designs/2026-05-15-creem-payment-integration-design.md`
- [ ] 在 `backend/.env` 配置 Creem Test Mode 所需变量（先用测试 key）
- [ ] 确认本地前后端可启动（frontend:5173 / backend:8000）
- [ ] 跑一轮基线检查（后端最小：`ruff check + mypy`，前端最小：`lint + typecheck`）

## 任务列表

### 任务 1: 扩展后端配置项与地区常量 (~3 min)
- 描述: 增加 Creem 相关环境变量、地区分组常量与定价系数配置读取。
- 文件:
  - 修改 `backend/app/core/config.py`
  - 修改 `backend/.env.example`
- 测试: 配置加载单测（缺失可选值时默认行为正确）。
- 验证: 启动时配置对象包含 `CREEM_*`、`PREMIUM_REGIONS`、`DEVELOPING_REGIONS`。
- 依赖: 无

### 任务 2: users 表增加订阅/地区字段 + 迁移 (~4 min)
- 描述: 按设计为 `users` 增加 subscription/pricing 字段并设置默认值。
- 文件:
  - 修改 `backend/app/db/models/*.py`（users 模型所在文件）
  - 创建 `backend/alembic/versions/*_add_creem_subscription_fields.py`
- 测试: 迁移 smoke（upgrade 可执行）；模型字段映射检查。
- 验证: `alembic upgrade head` 后字段存在且默认值生效。
- 依赖: 任务 1

### 任务 3: 新建 Creem API 客户端 (~4 min)
- 描述: 封装创建 Checkout、查询/取消订阅能力，统一超时与错误映射。
- 文件:
  - 创建 `backend/app/integrations/creem/client.py`
  - 创建 `backend/app/integrations/creem/__init__.py`
- 测试: 对 client 的 HTTP mock 测试（成功、超时、4xx/5xx）。
- 验证: 调用层可拿到标准化结果/异常。
- 依赖: 任务 1

### 任务 4: 支付服务层（业务编排）(~5 min)
- 描述: 实现创建 checkout payload、地区判定、订阅状态读取与取消逻辑。
- 文件:
  - 创建 `backend/app/services/payments/service.py`
  - （如需要）创建/修改 `backend/app/services/payments/types.py`
- 测试: service 单测覆盖地区映射、未登录保护、checkout 参数生成。
- 验证: service 输出满足 API contract（checkout_url/status/region pricing）。
- 依赖: 任务 2、任务 3

### 任务 5: Webhook 处理与签名校验 (~5 min)
- 描述: 实现 `creem` webhook 验签、事件分发、幂等更新用户订阅/代币。
- 文件:
  - 创建 `backend/app/services/payments/webhook_handler.py`
  - （如已有通用异常）修改 `backend/app/core/exceptions.py`
- 测试: 验签失败 401、重复事件幂等、支付成功状态更新。
- 验证: 同一事件重复投递不会重复发币或重复变更订阅。
- 依赖: 任务 2、任务 3

### 任务 6: 新增 payments API 路由 (~5 min)
- 描述: 实现 6 个端点：checkout/webhook/subscription/cancel/region(get+put)。
- 文件:
  - 创建 `backend/app/api/v1/payments.py`
  - 修改 `backend/app/api/v1/__init__.py` 或路由注册文件
  - 创建 `backend/app/schemas/payments.py`
- 测试: API contract 测试（状态码、响应体、鉴权、错误码）。
- 验证: OpenAPI 出现新端点，鉴权与错误映射符合设计。
- 依赖: 任务 4、任务 5

### 任务 7: 后端测试补齐 (~4 min)
- 描述: 补 service + API + webhook 核心路径测试。
- 文件:
  - 创建/修改 `backend/tests/services/test_payments_service.py`
  - 创建/修改 `backend/tests/api/test_payments_api.py`
- 测试: checkout 成功、未登录 401、creem 超时 503、region fallback、cancel 成功。
- 验证: 目标测试文件全部通过。
- 依赖: 任务 6

### 任务 8: 前端支付 API 封装 (~3 min)
- 描述: 新增 payment API 调用方法与类型定义。
- 文件:
  - 创建 `frontend/src/api/payments.ts`
  - （如有统一导出）修改 `frontend/src/api/index.ts`
- 测试: API 模块单测（请求路径、method、payload）。
- 验证: 页面层可直接调用 `createCheckout/getRegion/updateRegion/...`。
- 依赖: 任务 6

### 任务 9: 价格页接入地区与订阅结账 (~5 min)
- 描述: 加地区提示条、地区切换触发、本地价格展示、订阅 checkout 跳转。
- 文件:
  - 修改 `frontend/src/pages/DungeonScholarPricingPage.vue`
  - （如抽离）创建 `frontend/src/components/pricing/*`
- 测试: 组件行为测试（切换地区后价格变化；点击跳转 checkout_url）。
- 验证: 价格随 region 更新，按钮跳转正确 URL。
- 依赖: 任务 8

### 任务 10: 商城页代币充值跳转 checkout (~3 min)
- 描述: 将购买代币按钮改为请求 checkout 并跳转。
- 文件:
  - 修改 `frontend/src/pages/DungeonScholarShopPage.vue`
- 测试: 点击充值触发 API 并重定向。
- 验证: 不再本地扣逻辑，统一走后端 checkout。
- 依赖: 任务 8

### 任务 11: 设置页订阅管理与地区切换 (~5 min)
- 描述: 展示订阅状态、取消订阅入口、手动切换地区入口。
- 文件:
  - 修改 `frontend/src/pages/DungeonScholarSettingsPage.vue`
  - （可选）创建 `frontend/src/components/settings/SubscriptionSection.vue`
- 测试: 状态展示、取消订阅按钮行为、地区切换提交。
- 验证: 设置页可完整管理订阅与地区。
- 依赖: 任务 8

### 任务 12: 前端文案与错误提示补齐 (~3 min)
- 描述: 增加支付/地区相关中英文文案与错误反馈。
- 文件:
  - 修改 `frontend/src/i18n/index.ts`（或项目实际 i18n 文件）
- 测试: 文案 key 存在性检查（避免 missing key）。
- 验证: UI 无裸 key，错误信息可读。
- 依赖: 任务 9、任务 10、任务 11

### 任务 13: 联调与最终验证 (~5 min)
- 描述: 端到端走 Creem Test Mode：checkout→webhook→状态回写。
- 文件: 无业务文件变更（仅必要测试修正）
- 测试:
  - 后端：`uv run ruff check app tests`、`uv run mypy app`、`uv run pytest tests/api/test_payments_api.py tests/services/test_payments_service.py -q`
  - 前端：`npm run lint`、`npm run typecheck`、`npm run test -- <相关spec>`
- 验证: 代币到账、订阅状态变更、地区价格切换全链路通过。
- 依赖: 任务 7、任务 12

## 并行机会
- 可并行 A：任务 3（Creem client）与任务 2（DB 迁移）可并行。
- 可并行 B：任务 9（价格页）、任务 10（商城页）、任务 11（设置页）在任务 8 完成后可并行。
- 可并行 C：任务 7（后端测试补齐）可与前端任务 9~11 后半段穿插推进。

## 风险 & 缓解
| 风险 | 概率 | 影响 | 缓解措施 |
|---|---|---|---|
| Webhook 重放导致重复发币 | 中 | 高 | 事件幂等键 + 已处理检查 |
| Creem API 不稳定/超时 | 中 | 中 | 超时重试策略 + 503 明确提示 |
| 地区判定误差影响价格 | 中 | 中 | fallback `standard` + 用户手动切换 |
| 前后端价格计算不一致 | 低 | 高 | 以后端返回价格为准，前端仅展示 |
| 订阅状态回写延迟 | 中 | 中 | 设置页提供“刷新状态”按钮与轮询兜底 |

## 测试策略
| 层级 | 内容 | 覆盖目标 |
|---|---|---|
| 后端单元测试 | region 分类、checkout 参数组装、webhook 事件处理 | 核心逻辑分支 |
| 后端 API 测试 | 鉴权、状态码、错误映射、响应结构 | 所有新端点 contract |
| 前端组件测试 | 地区切换、价格刷新、checkout 跳转、订阅管理交互 | 主流程行为 |
| 集成测试 | Creem Test Mode 全链路 | 支付成功回写真实性能 |
