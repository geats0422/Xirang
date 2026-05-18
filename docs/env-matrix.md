# 环境变量矩阵

本矩阵只记录变量名、用途、归属平台、一致性要求和验证方式，不记录真实 secret 值。真实 secret 仅保存在 Vercel Dashboard、Render Dashboard 或本地未跟踪 `.env` 文件中。

## Vercel Frontend

| 变量 | 是否 secret | 生产策略 | 验证方式 |
|---|---|---|---|
| `VITE_API_BASE_URL` | 否 | 使用 Vercel rewrite 时保持空；显式配置时不得重复包含 `/api/v1` | 浏览器 Network 检查 API URL |
| `VITE_API_PROXY_TARGET` | 否 | 本地开发用；生产通常不配置 | Vite dev proxy |
| `VITE_ENABLE_BACKEND_HEALTH_CHECK` | 否 | 生产建议 `true` | 登录页健康检查 |
| `VITE_APP_BASE_URL` | 否 | 当前 Vercel 主域名 | OAuth/回跳场景 |
| `VITE_DEFAULT_MODEL` | 否 | 与后端默认模型策略一致 | 前端模型选择 |
| `VITE_MODEL_PROVIDER_CONFIG` | 否 | 仅公开可展示 provider/model 信息，不写 secret | 前端配置加载 |

## Render API

| 变量 | 是否 secret | 与 Worker 一致 | 用途 | 验证方式 |
|---|---|---:|---|---|
| `APP_ENV` | 否 | 建议一致 | 选择运行环境 | 启动日志 |
| `LOG_LEVEL` | 否 | 可不同 | 日志等级 | Render logs |
| `BACKEND_BASE_URL` | 否 | API-only | 当前 API 域名 | OAuth callback / webhook URL |
| `FRONTEND_BASE_URL` | 否 | API-only | 当前 Vercel 主域名 | OAuth 回跳、支付成功页 |
| `DATABASE_URL` | 是 | 是 | Supabase PostgreSQL | `/api/v1/health/ready`、迁移日志 |
| `SECRET_KEY` | 是 | 是 | JWT 与验证码签名 | 登录、注册验证码 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | API-only | access token TTL | 登录响应 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 否 | API-only | refresh token TTL | refresh 流程 |
| `CORS_ORIGINS` | 否 | API-only | 允许的前端来源 | 浏览器 CORS 请求 |
| `STORAGE_MODE` | 否 | 是 | local/R2 存储模式 | 上传/读取文件 |
| `UPLOAD_DIR` | 否 | 本地模式一致 | local 存储目录 | 上传文件路径 |
| `MAX_FILE_SIZE_MB` | 否 | API-only | 上传大小限制 | 上传大文件 |

## Render Worker

| 变量 | 是否 secret | 与 API 一致 | 用途 | 验证方式 |
|---|---|---:|---|---|
| `APP_ENV` | 否 | 建议一致 | 选择运行环境 | Worker logs |
| `LOG_LEVEL` | 否 | 可不同 | 日志等级 | Worker logs |
| `DATABASE_URL` | 是 | 是 | 读取/更新 jobs、documents | job 状态推进 |
| `SECRET_KEY` | 是 | 是 | 共用安全配置 | Worker 启动 |
| `STORAGE_MODE` | 否 | 是 | 读取上传文件 | ingestion job |
| `UPLOAD_DIR` | 否 | 本地模式一致 | local 文件目录 | ingestion job |
| `WORKER_POLL_INTERVAL_SECONDS` | 否 | Worker-only | 轮询间隔 | Worker logs |
| `WORKER_MAX_CONCURRENT_JOBS` | 否 | Worker-only | 并发任务数 | Worker logs |

## Storage / R2

| 变量 | 是否 secret | API | Worker | 用途 |
|---|---|---:|---:|---|
| `R2_BUCKET_NAME` | 否 | 是 | 是 | R2 bucket 名称 |
| `R2_ACCOUNT_ID` | 否 | 是 | 是 | Cloudflare account id |
| `R2_ACCESS_KEY_ID` | 是 | 是 | 是 | R2 access key |
| `R2_SECRET_ACCESS_KEY` | 是 | 是 | 是 | R2 secret key |
| `R2_PUBLIC_URL` | 否 | 是 | 是 | 文件公开访问 URL |

## LLM / OCR / Indexing

| 变量 | 是否 secret | API | Worker | 用途 |
|---|---|---:|---:|---|
| `NVIDIA_API_KEY` | 是 | 是 | 是 | NVIDIA LLM 调用 |
| `NVIDIA_BASE_URL` | 否 | 是 | 是 | NVIDIA API base |
| `NVIDIA_MODEL` | 否 | 是 | 是 | 默认模型 |
| `OPENAI_API_KEY` | 是 | 是 | 是 | OpenAI 调用 |
| `OPENAI_BASE_URL` | 否 | 是 | 是 | OpenAI API base |
| `OPENAI_MODEL` | 否 | 是 | 是 | 默认模型 |
| `PAGEINDEX_URL` | 否 | 可选 | 是 | PageIndex 服务地址 |
| `PAGEINDEX_MOCK_FALLBACK` | 否 | 可选 | 可选 | PageIndex 不可用时是否 mock fallback |
| `MINERU_URL` | 否 | 是 | 是 | MinerU 服务地址 |
| `MINERU_TIMEOUT_SECONDS` | 否 | 是 | 是 | MinerU 解析超时 |
| `MINERU_BACKEND` | 否 | 是 | 是 | MinerU backend |
| `MINERU_LANG_LIST` | 否 | 是 | 是 | MinerU 语言配置 |

`PAGEINDEX_URL` 语义必须显式标注：

- `mock`: 不依赖真实 PageIndex，仅用于开发或降级。
- `local`: 指向本地服务，只能用于本机开发。
- `external web service`: 指向 Render/其他平台部署的 HTTP PageIndex 服务。
- `worker`: 仅代表后台任务形态，不等于有 HTTP health endpoint。

## OAuth

| 变量 | 是否 secret | API | Worker | 用途 |
|---|---|---:|---:|---|
| `GITHUB_CLIENT_ID` | 否 | 是 | 否 | GitHub OAuth |
| `GITHUB_CLIENT_SECRET` | 是 | 是 | 否 | GitHub OAuth |
| `GITHUB_CALLBACK_URL` | 否 | 是 | 否 | GitHub callback |
| `GOOGLE_CLIENT_ID` | 否 | 是 | 否 | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | 是 | 是 | 否 | Google OAuth |
| `GOOGLE_CALLBACK_URL` | 否 | 是 | 否 | Google callback |
| `MICROSOFT_CLIENT_ID` | 否 | 是 | 否 | Microsoft OAuth |
| `MICROSOFT_CLIENT_SECRET` | 是 | 是 | 否 | Microsoft OAuth |
| `MICROSOFT_TENANT_ID` | 否 | 是 | 否 | Microsoft tenant |
| `MICROSOFT_CALLBACK_URL` | 否 | 是 | 否 | Microsoft callback |

## Resend / Email Verification

| 变量 | 是否 secret | API | Worker | 用途 |
|---|---|---:|---:|---|
| `RESEND_API_KEY` | 是 | 是 | 否 | 发送注册验证码 |
| `RESEND_FROM_EMAIL` | 否 | 是 | 否 | 已验证域名发件人，例如 `Xirang <noreply@xiranglearn.quest>` |
| `RESEND_TIMEOUT_SECONDS` | 否 | 是 | 否 | Resend 请求超时 |
| `VERIFICATION_CODE_SECRET` | 是 | 是 | 否 | 验证码 HMAC secret |
| `VERIFICATION_CODE_TTL_SECONDS` | 否 | 是 | 否 | 验证码有效期 |
| `VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS` | 否 | 是 | 否 | 重发冷却 |
| `VERIFICATION_CODE_MAX_ATTEMPTS` | 否 | 是 | 否 | 最大尝试次数 |

## Creem Payments

| 变量 | 是否 secret | API | Worker | 用途 |
|---|---|---:|---:|---|
| `CREEM_API_KEY` | 是 | 是 | 否 | Creem API 调用 |
| `CREEM_WEBHOOK_SECRET` | 是 | 是 | 否 | Webhook 签名校验 |
| `CREEM_API_BASE_URL` | 否 | 是 | 否 | Creem API base |
| `CREEM_TIMEOUT_SECONDS` | 否 | 是 | 否 | Creem 请求超时 |
| `CREEM_CHECKOUT_SUCCESS_URL` | 否 | 是 | 否 | checkout 成功跳转 |
| `CREEM_CHECKOUT_CANCEL_URL` | 否 | 是 | 否 | checkout 取消跳转 |
| `CREEM_WEBHOOK_PATH` | 否 | 是 | 否 | webhook path |
| `CREEM_PRICE_PREMIUM_MULTIPLIER` | 否 | 是 | 否 | premium 定价系数 |
| `CREEM_PRICE_STANDARD_MULTIPLIER` | 否 | 是 | 否 | standard 定价系数 |
| `CREEM_PRICE_DEVELOPING_MULTIPLIER` | 否 | 是 | 否 | developing 定价系数 |
| `CREEM_PREMIUM_REGIONS` | 否 | 是 | 否 | premium 国家列表 |
| `CREEM_DEVELOPING_REGIONS` | 否 | 是 | 否 | developing 国家列表 |
| `CREEM_PRODUCT_COIN_60` | 否 | 是 | 否 | 60 代币 Product ID |
| `CREEM_PRODUCT_COIN_300` | 否 | 是 | 否 | 300 代币 Product ID |
| `CREEM_PRODUCT_COIN_680` | 否 | 是 | 否 | 680 代币 Product ID |
| `CREEM_PRODUCT_COIN_1500` | 否 | 是 | 否 | 1500 代币 Product ID |
| `CREEM_PRODUCT_COIN_3500` | 否 | 是 | 否 | 3500 代币 Product ID |
| `CREEM_PRODUCT_SUB_MONTHLY` | 否 | 是 | 否 | 月付 Product ID |
| `CREEM_PRODUCT_SUB_QUARTERLY` | 否 | 是 | 否 | 季付 Product ID |
| `CREEM_PRODUCT_SUB_YEARLY` | 否 | 是 | 否 | 年付 Product ID |

## 一致性规则

- `frontend/vercel.json` 的 API rewrite、Render `BACKEND_BASE_URL`、OAuth callback URL 必须使用同一 API 域名。
- `CORS_ORIGINS` 必须包含当前 Vercel 主域名。
- `FRONTEND_BASE_URL` 与 `VITE_APP_BASE_URL` 必须指向同一主前端域名。
- API 与 Worker 的 `DATABASE_URL`、`STORAGE_MODE`、R2、LLM provider 变量应一致。
- Worker 不应依赖 Web-only OAuth、Creem checkout 或 CORS 配置。
- Dashboard 中任意变量变更后，必须同步检查 `docs/deployment-checklist.md`、`docs/render-blueprint-template.md` 和 `docs/smoke-checklist.md`。
