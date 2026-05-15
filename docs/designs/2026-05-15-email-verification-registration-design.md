# 邮箱验证码注册设计文档

## 目标
使用 Resend 实现注册邮箱验证码：用户必须先完成邮箱验证码校验，后端才创建账号并签发登录 token。

## 用户场景
用户进入注册页，填写邮箱并请求验证码。收到邮件后，用户输入验证码、用户名、密码和确认密码，提交注册。后端验证验证码有效后创建账号，设置 `email_verified_at`，创建默认资料/设置/钱包，并返回登录凭证。

## 技术方案
采用“先验证邮箱，再创建账号”流程。

- 注册页新增验证码输入和“发送验证码”按钮。
- 后端新增发送验证码接口，使用 Resend 邮件 API 发验证码。
- 后端新增验证码校验逻辑，注册接口要求携带验证码。
- 验证码只存哈希，不存明文。
- 验证码有过期时间、最大尝试次数和重新发送冷却时间。
- OAuth 注册/登录流程不受影响。

推荐默认策略：

- 验证码长度：6 位数字。
- 有效期：10 分钟。
- 重发冷却：60 秒。
- 单个验证码最大校验次数：5 次。
- 邮件发送使用 `Idempotency-Key`，避免重复请求造成重复邮件。

## 数据模型
新增表 `email_verification_codes`：

- `id`: UUID 主键。
- `email_normalized`: 小写邮箱。
- `code_hash`: 验证码哈希。
- `purpose`: `registration`，预留将来扩展到改邮箱/找回密码。
- `attempt_count`: 已尝试次数。
- `max_attempts`: 最大尝试次数，默认 5。
- `expires_at`: 过期时间。
- `consumed_at`: 使用成功时间。
- `created_at`: 创建时间。
- `last_sent_at`: 最近发送时间。

索引：

- `email_normalized + purpose + created_at`，用于查询最新验证码。
- 可选部分索引：未消费验证码。

不在用户表中创建未验证账号。注册成功时设置 `users.email_verified_at = now()`。

## 接口设计
新增接口：

`POST /api/v1/auth/register/code`

请求：

```json
{
  "email": "user@example.com"
}
```

响应：

```json
{
  "ok": true,
  "expires_in_seconds": 600,
  "resend_after_seconds": 60
}
```

行为：

- 如果邮箱已注册，返回 409。
- 如果 60 秒内重复请求，返回 429。
- 生成验证码，保存哈希，调用 Resend 发邮件。

修改接口：

`POST /api/v1/auth/register`

请求新增字段：

```json
{
  "username": "alice",
  "email": "user@example.com",
  "password": "StrongPass123",
  "verification_code": "123456"
}
```

行为：

- 先校验验证码。
- 验证码通过后再检查用户名/邮箱唯一性并创建账号。
- 创建用户时设置 `email_verified_at`。
- 返回现有 `user + tokens` 响应结构。

Resend 配置：

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_TIMEOUT_SECONDS`
- `EMAIL_VERIFICATION_TTL_SECONDS`
- `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS`

## 错误处理
- 邮箱已注册：409。
- 验证码未发送/不存在：400。
- 验证码错误：400，并增加尝试次数。
- 验证码过期：400。
- 验证码尝试次数耗尽：429。
- 发送过于频繁：429。
- Resend 未配置或发送失败：503。

安全注意事项：

- 响应不返回验证码。
- 日志不记录验证码明文。
- 验证码哈希使用现有密码哈希服务或 HMAC-SHA256 + `SECRET_KEY`。
- 邮箱统一 lower/trim。

## 前端交互
注册页新增验证码区域：

- 邮箱输入框旁或下方显示“发送验证码”。
- 点击发送前校验邮箱格式。
- 发送后按钮倒计时 60 秒。
- 注册提交时要求验证码非空。
- 注册成功后沿用现有登录态持久化和跳转首页。

建议文案：

- 发送按钮：`Send code` / `发送验证码`
- 倒计时：`Resend in 59s` / `59 秒后重发`
- 输入框：`Verification code` / `验证码`

## 测试策略
后端：

- 发送验证码成功：写入哈希记录并调用邮件服务。
- 重复发送冷却：返回 429。
- 已注册邮箱发送验证码：返回 409。
- 注册缺少验证码：422。
- 注册验证码错误：400，尝试次数增加。
- 注册验证码过期：400。
- 注册验证码正确：创建用户，`email_verified_at` 非空，返回 token。
- Resend 发送失败：返回 503，不创建用户。

前端：

- 注册页渲染验证码输入和发送按钮。
- 点击发送验证码调用 API。
- 发送后倒计时禁用按钮。
- 注册提交携带 `verification_code`。
- 验证码为空时显示字段错误。

## 非目标
- 不实现找回密码验证码。
- 不实现邮箱修改验证码。
- 不限制 OAuth 用户登录。
- 不引入营销邮件订阅体系。
