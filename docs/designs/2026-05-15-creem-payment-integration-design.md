# Creem 支付集成设计文档

## 目标
接入 Creem 作为 Merchant of Record，实现代币充值和订阅付费，支持地区差异化定价。

## 用户场景
1. **代币充值**：用户在价格页/商城页选择档位 → 跳转 Creem Checkout → 支付成功 → 代币自动到账
2. **订阅 Pro**：用户在价格页选择周期 → 跳转 Creem Checkout（7天试用） → 支付成功 → 获得 Pro 权益
3. **地区切换**：用户看到顶部提示"检测到您在中国" → 点击切换 → 选择国家 → 价格自动更新
4. **订阅管理**：用户在设置页查看订阅状态 → 取消订阅/升级周期

## 技术方案

### 后端（FastAPI）
- 新增 `app/integrations/creem/client.py`：Creem API 客户端（创建 Checkout、查询订阅）
- 新增 `app/api/v1/payments.py`：支付相关 API（创建 Checkout、Webhook 处理）
- 扩展 `users` 表：新增订阅和地区字段
- 新增 `app/core/config.py` 配置项：Creem API Key、Webhook Secret、地区列表

### 前端（Vue 3）
- 价格页：地区自动检测 + 顶部提示条 + 本地货币展示 + 跳转 Creem Checkout
- 商城页：代币充值按钮改为跳转 Creem Checkout
- 设置页：新增"订阅管理"入口（查看状态/取消订阅/切换地区）

## 数据模型

### `users` 表扩展字段
```sql
subscription_status VARCHAR(20) DEFAULT 'free'  -- free/pro/trialing/past_due/canceled
subscription_tier VARCHAR(20)                   -- monthly/quarterly/yearly
subscription_expires_at TIMESTAMPTZ
creem_customer_id VARCHAR(100)
creem_subscription_id VARCHAR(100)
pricing_region VARCHAR(20) DEFAULT 'standard'   -- premium/standard/developing
```

### 地区国家列表（后端配置）
```python
PREMIUM_REGIONS = {"US", "GB", "CA", "AU", "DE", "FR", "JP", "SG", "NL", "SE", "CH", "NO", "DK", "FI", "IE", "NZ", "BE", "AT", "IT", "ES"}
DEVELOPING_REGIONS = {"IN", "ID", "PH", "VN", "TH", "MY", "BR", "MX", "AR", "CO", "PE", "EG", "NG", "KE", "PK", "BD", "UA", "RO", "BG"}
# 其余为 standard
```

### 定价系数
| 地区 | 系数 | 月付 | 季付 | 年付 |
|---|---|---|---|---|
| premium | 1.2 | $9.60 | $24.00 | $84.00 |
| standard | 1.0 | $8.00 | $20.00 | $70.00 |
| developing | 0.5 | $4.00 | $10.00 | $35.00 |

## 接口设计

### 后端 API
| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/v1/payments/checkout` | POST | 创建 Checkout，返回 checkout_url |
| `/api/v1/payments/webhook/creem` | POST | 接收 Creem Webhook |
| `/api/v1/payments/subscription` | GET | 获取当前用户订阅状态 |
| `/api/v1/payments/subscription/cancel` | POST | 取消订阅（scheduled） |
| `/api/v1/payments/region` | GET | 获取用户地区及对应价格 |
| `/api/v1/payments/region` | PUT | 手动切换地区 |

### 前端组件变更
| 组件 | 变更 |
|---|---|
| `DungeonScholarPricingPage.vue` | 地区检测横幅、本地货币展示、跳转 Creem Checkout |
| `DungeonScholarShopPage.vue` | 代币充值改为跳转 Creem Checkout |
| `DungeonScholarSettingsPage.vue` | 新增订阅管理区块、地区切换 |

## 错误处理
- **Webhook 验证失败**：返回 401，记录日志
- **Creem API 超时**：返回 503，前端提示稍后重试
- **用户未登录创建 Checkout**：返回 401
- **地区列表未命中**：默认 standard

## 测试策略
- 后端：Mock Creem API，测试 Checkout 创建、Webhook 处理、地区判断逻辑
- 前端：Mock 支付 API，测试地区切换、价格展示、跳转逻辑
- 集成：使用 Creem Test Mode 进行端到端测试
