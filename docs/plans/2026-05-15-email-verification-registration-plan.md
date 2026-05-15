# 邮箱验证码注册实施计划

## 总览

基于 `docs/designs/2026-05-15-email-verification-registration-design.md`，实现“先验证邮箱，再创建账号”的注册流程。后端新增验证码存储、发送、校验能力，并将注册接口改为必须携带验证码；前端注册页新增发送验证码、倒计时、验证码输入和提交校验。

关键决策：

- 验证码明文仅用于发送邮件，不入库。
- 入库保存 HMAC-SHA256 后的验证码。
- OAuth 注册/登录流程保持不变。
- 注册成功时设置 `users.email_verified_at`。

## 任务列表

- [ ] 任务 1: 新增邮箱验证码数据库模型与迁移
- [ ] 任务 2: 扩展认证配置项
- [ ] 任务 3: 新增 Resend 邮件客户端
- [ ] 任务 4: 扩展 AuthRepository 验证码读写能力
- [ ] 任务 5: 实现验证码生成、哈希与校验服务逻辑
- [ ] 任务 6: 注册创建用户时设置邮箱已验证时间
- [ ] 任务 7: 扩展后端 Auth schema
- [ ] 任务 8: 新增发送验证码 API 并修改注册 API
- [ ] 任务 9: 编写后端服务层验证码测试
- [ ] 任务 10: 编写后端 API 层验证码测试
- [ ] 任务 11: 扩展前端 Auth API 方法
- [ ] 任务 12: 注册页新增验证码状态与校验
- [ ] 任务 13: 注册页新增发送验证码按钮与倒计时
- [ ] 任务 14: 增加前端 i18n 文案
- [ ] 任务 15: 前后端最终验证

## 详细任务

### 任务 1: 新增邮箱验证码数据库模型与迁移

- 修改 `backend/app/db/models/auth.py`
- 创建 Alembic 迁移，新增 `email_verification_codes` 表
- 字段：`id`、`email_normalized`、`code_hash`、`purpose`、`attempt_count`、`max_attempts`、`expires_at`、`consumed_at`、`last_sent_at`、`created_at`

### 任务 2: 扩展认证配置项

- 修改 `backend/app/core/config.py`
- 修改 `backend/.env.example`
- 新增 `RESEND_API_KEY`、`RESEND_FROM_EMAIL`、`RESEND_TIMEOUT_SECONDS`、`EMAIL_VERIFICATION_TTL_SECONDS`、`EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS`、`EMAIL_VERIFICATION_MAX_ATTEMPTS`

### 任务 3: 新增 Resend 邮件客户端

- 创建 `backend/app/integrations/resend/client.py`
- 创建 `backend/app/integrations/resend/__init__.py`
- 支持未配置、发送失败、超时错误

### 任务 4: 扩展 AuthRepository 验证码读写能力

- 修改 `backend/app/repositories/auth_repository.py`
- 支持创建验证码、查询最新验证码、增加尝试次数、标记消费

### 任务 5: 实现验证码生成、哈希与校验服务逻辑

- 修改 `backend/app/services/auth/service.py`
- 生成 6 位数字验证码
- 使用 HMAC-SHA256 保存验证码哈希
- 实现冷却、过期、尝试次数、消费校验

### 任务 6: 注册创建用户时设置邮箱已验证时间

- 修改 `backend/app/repositories/auth_repository.py`
- 修改 `backend/app/services/auth/service.py`
- 注册成功时写入 `email_verified_at`

### 任务 7: 扩展后端 Auth schema

- 修改 `backend/app/schemas/auth.py`
- `RegisterRequest` 新增 `verification_code`
- 新增 `RegisterCodeRequest` 和 `RegisterCodeResponse`

### 任务 8: 新增发送验证码 API 并修改注册 API

- 修改 `backend/app/api/v1/auth.py`
- 新增 `POST /api/v1/auth/register/code`
- 注册接口传入验证码并映射验证码相关错误码

### 任务 9: 编写后端服务层验证码测试

- 修改 `backend/tests/services/test_auth_service.py`
- 覆盖发送验证码、冷却、错误验证码、过期、次数耗尽、正确注册

### 任务 10: 编写后端 API 层验证码测试

- 修改 `backend/tests/api/test_auth_api.py`
- 覆盖 HTTP contract 和错误码映射

### 任务 11: 扩展前端 Auth API 方法

- 修改 `frontend/src/api/auth.ts`
- 注册请求 body 包含 `verification_code`
- 新增 `sendRegisterVerificationCode`

### 任务 12: 注册页新增验证码状态与校验

- 修改 `frontend/src/pages/DungeonScholarLoginPage.vue`
- 注册模式显示验证码输入
- 验证码为空时显示字段错误

### 任务 13: 注册页新增发送验证码按钮与倒计时

- 修改 `frontend/src/pages/DungeonScholarLoginPage.vue`
- 发送成功后 60 秒倒计时

### 任务 14: 增加前端 i18n 文案

- 修改 `frontend/src/i18n/index.ts`
- 添加验证码输入、发送按钮、倒计时、错误提示中英文文案

### 任务 15: 前后端最终验证

- 后端：`uv run ruff check app tests`、`uv run mypy app`、认证相关测试
- 前端：`npm run lint`、`npm run typecheck`、注册页相关测试

## 风险与缓解

- Resend 未配置导致本地测试失败：服务层使用 fake mail client 测试，真实发送仅依赖配置。
- 验证码明文进入日志：禁止记录验证码，仅记录请求结果。
- 注册接口变更破坏前端：同批更新前端注册 payload。
- OAuth 被误要求验证码：仅修改邮箱密码注册路径。
