# 任务系统（Quest System）设计规格

**版本**: 1.0  
**日期**: 2026-04-09  
**状态**: 已批准  
**范围**: Phase 2 核心功能

---

## 1. 背景与目标

### 1.1 问题陈述

当前 Quests 页面存在以下问题：

| 问题 | 当前状态 |
|------|---------|
| 消息弹窗未接入 i18n | NotificationPopover 部分已用 i18n，但数据源未对接 |
| 消息状态与数据库不匹配 | notifications 是硬编码空数组 |
| 每日任务未每日更新 | 使用 localStorage 模拟，依赖前端计算 |
| 月度任务进度不同步 | 存储在 localStorage，与每日完成进度可能不同步 |
| 剩余时间计算错误 | `totalDaysInMonth - now.getDate()` 在月初显示错误（如4月3日显示27天而非实际剩余27天） |
| 快捷按钮无反馈 | 上传按钮无跳转，领取奖励按钮无逻辑 |

### 1.2 目标

- 实现**后端任务系统**，数据真实存储在 PostgreSQL
- 实现**消息通知系统**，支持任务奖励、连胜提醒、过期提醒等
- **最小化实现**：复用 Phase 1 现有表结构，快速上线核心功能
- 支持**简体中文（zh-CN）**和**英文（en）**两种语言

---

## 2. 技术方案

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                         │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ QuestsPage       │    │ NotificationPopover         │  │
│  │  • 任务卡片展示   │    │  • 消息列表                  │  │
│  │  • 进度条        │    │  • 空状态                    │  │
│  │  • 快捷按钮      │    │                              │  │
│  └────────┬─────────┘    └──────────────────────────────┘  │
│           │                        │                        │
│           ▼                        ▼                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Service Layer (quests.ts)            │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────┘
                         │ HTTP /api/v1/quests, /api/v1/notifications
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ quest_api    │  │ notify_api  │  │ runs/documents   │   │
│  │ /quests      │  │ /notifications│  │ 聚合查询          │   │
│  │ /claim       │  │              │  │                  │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                │                    │              │
│         ▼                ▼                    ▼              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Service Layer (quest_service)            │   │
│  │  • get_user_quests()   • claim_reward()              │   │
│  │  • get_notifications() • daily_reset()              │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Repository Layer                         │   │
│  │  • quest_repository   • notification_repository      │   │
│  │  • run_repository     • document_repository         │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Database (PostgreSQL)                     │   │
│  │  • quest_assignments  (NEW)                          │   │
│  │  • notifications       (NEW)                         │   │
│  │  • wallet_ledger      (EXIST - 奖励发放)            │   │
│  │  • runs/documents      (EXIST - 进度数据源)          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 方案选择：最小化实现

**理由**：
1. 风险可控，与 Phase 1 兼容
2. 快速验证核心流程
3. 可复用 `wallet_ledger` 发放奖励

---

## 3. 数据库设计

### 3.1 新增表

#### `quest_assignments` — 用户任务分配表

```sql
CREATE TABLE quest_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  quest_code VARCHAR(60) NOT NULL,
  quest_type VARCHAR(20) NOT NULL DEFAULT 'daily',
  target_metric VARCHAR(60) NOT NULL,
  target_value INTEGER NOT NULL DEFAULT 1,
  progress_value INTEGER NOT NULL DEFAULT 0,
  cycle_key VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
  reward_type VARCHAR(20) NOT NULL DEFAULT 'asset',
  reward_asset_code VARCHAR(40),
  reward_quantity INTEGER NOT NULL DEFAULT 0,
  reward_item_code VARCHAR(80),
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  claimed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, quest_code, cycle_key),
  CHECK (quest_type IN ('daily', 'monthly', 'special')),
  CHECK (status IN ('in_progress', 'completed', 'claimed', 'expired')),
  CHECK (reward_type IN ('asset', 'item'))
);

CREATE INDEX ix_quest_assignments_user_status ON quest_assignments(user_id, status);
CREATE INDEX ix_quest_assignments_user_cycle ON quest_assignments(user_id, cycle_key);
```

**设计要点**：

| 字段 | 说明 |
|------|------|
| `quest_code` | 任务唯一标识，如 `quest-upload`、`quest-abyss` |
| `target_metric` | 进度来源指标，后端据此从 runs/documents/wallet 聚合 |
| `cycle_key` | 自然日 `"2026-04-09"` 或自然月 `"2026-04"` |
| `status` 四状态 | `in_progress` → `completed` → `claimed` / `expired` |
| `reward_*` | 任务级别的奖励定义，claim 时写入 `wallet_ledger` |
| 唯一约束 | 同一用户+同一任务+同一周期只允许一条记录 |

#### `notifications` — 用户消息通知表

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(40) NOT NULL,
  title VARCHAR(255) NOT NULL,
  body TEXT,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  related_quest_id UUID,
  action_url VARCHAR(500),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  read_at TIMESTAMPTZ
);

CREATE INDEX ix_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
```

**设计要点**：

| 字段 | 说明 |
|------|------|
| `type` | 通知类型枚举（见 3.3） |
| `is_read` + `read_at` | 已读状态追踪 |
| `related_quest_id` | 可关联任务，前端可跳转 |
| `action_url` | 深度链接，如 `/quests?action=claim&id=xxx` |
| 部分索引 | `WHERE is_read = FALSE` 只索引未读记录 |

### 3.2 现有表复用

- `wallet_ledger` — 奖励发放（reason_code = `quest_claim`）
- `inventories` — 道具发放（已有 item_code 字段）
- `runs` — 进度数据源（mode, status, ended_at, score 等）
- `documents` — 进度数据源（created_at）
- `users` — 用户信息
- `user_settings` — 语言偏好（language_code）

### 3.3 通知类型枚举

| type | 触发时机 | 示例 |
|------|----------|------|
| `quest_reward` | 任务完成可领取时 | "任务奖励可领取" |
| `quest_claimed` | 奖励领取成功时 | "奖励已领取" |
| `streak_warning` | 连胜即将中断时（当天23:00未完成） | "连胜即将中断！" |
| `streak_milestone` | 达到连胜里程碑（7天、15天、30天） | "连胜15天达成！" |
| `quest_expiring` | 每日任务即将过期时（22:00提醒） | "每日任务即将过期" |
| `monthly_milestone` | 月度进度里程碑（10/20/30） | "月度进度20/30" |
| `time_treasure` | 获得时间宝时 | "获得时间宝！" |
| `system` | 系统公告 | 动态 |

---

## 4. 任务定义

### 4.1 每日任务（6个）

| quest_code | 描述 | target_metric | target_value | 奖励 |
|------------|------|---------------|---------------|------|
| `quest-upload` | 上传1份新文档 | `document_upload` | 1 | 🧰 金箱道具 |
| `quest-streak` | 保持学习连胜 | `streak` | 1 | 🪙 +50 |
| `quest-abyss` | 深渊完成2次挑战 | `run_count_endless` | 2 | 🎁 翻倍卡（30分钟） |
| `quest-accuracy` | 单次答题正确率≥80% | `accuracy_gte_80` | 1 | 🪙 +30 |
| `quest-time` | 学习时长≥10分钟 | `study_minutes` | 10 | 🪙 +20 |
| `quest-floors` | 深渊到达5层 | `endless_floors` | 5 | 🪙 +25 |

### 4.2 游戏模式任务（3个）

| quest_code | 描述 | target_metric | target_value | 奖励 |
|------------|------|---------------|---------------|------|
| `quest-speed-clear` | 极速生存完成1局 | `run_count_speed` | 1 | ⏳ 时间宝·刻（10分钟） |
| `quest-draft-complete` | 知识牌局完成1局 | `run_count_draft` | 1 | ⏳ 时间宝·时（15分钟） |
| `quest-abyss-deep` | 深渊到达10层 | `endless_floors_gte_10` | 1 | ⏳ 时间宝·日（30分钟） |

### 4.3 里程碑任务

| quest_code | 描述 | target_metric | target_value | 奖励 |
|------------|------|---------------|---------------|------|
| `quest-streak-7` | 连续打卡7天 | `streak_days` | 7 | 🪙 +100 |
| `quest-streak-15` | 连续打卡15天 | `streak_days` | 15 | ⏳ 时间宝·日（30分钟）+ 🪙 +200 |
| `quest-streak-30` | 连续打卡30天 | `streak_days` | 30 | ⏳ 时间宝·日（30分钟）×2 + 🪙 +500 |

### 4.4 月度任务

| quest_code | 描述 | target_metric | target_value | 奖励 |
|------------|------|---------------|---------------|------|
| `quest-monthly` | 完成30个每日任务 | `daily_quests_completed` | 30 | 稀有道具+500🪙 |

### 4.5 时间宝（Time Treasure）道具设计

**三档时间宝**：

| item_code | 显示名 | 稀有度 | 效果 | 获取途径 |
|-----------|--------|--------|------|----------|
| `time_treasure_10` | 时间宝·刻 / Time Treasure·Quarter | `common` | 延长经验翻倍10分钟 | 极速生存完成1局 |
| `time_treasure_15` | 时间宝·时 / Time Treasure·Hourglass | `uncommon` | 延长经验翻倍15分钟 | 知识牌局完成1局 |
| `time_treasure_30` | 时间宝·日 / Time Treasure·Sundial | `rare` | 延长经验翻倍30分钟 | 深渊到达10层 / 连胜15天/30天 |

**时间宝与翻倍卡的叠加关系**：
- 翻倍卡（`xp_boost`）：激活30分钟经验翻倍
- 时间宝（任意档次）：延长当前翻倍效果的时长，**可累计叠加**
- 例：当前翻倍剩余15分钟 → 使用时间宝·刻（10分钟）→ 变成25分钟 → 再使用时间宝·日（30分钟）→ 变成55分钟
- 若当前无翻倍效果，使用时间宝无效（需先激活翻倍卡）

---

## 5. API 设计

### 5.1 任务相关 API

| 方法 | 路径 | 说明 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| GET | `/api/v1/quests` | 获取当前用户任务列表（含进度） | - | `QuestListResponse` |
| POST | `/api/v1/quests/{assignment_id}/claim` | 领取任务奖励 | - | `QuestClaimResponse` |
| GET | `/api/v1/quests/monthly-progress` | 获取月度进度 | - | `MonthlyProgressResponse` |

### 5.2 通知相关 API

| 方法 | 路径 | 说明 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| GET | `/api/v1/notifications` | 获取用户通知列表 | - | `NotificationListResponse` |
| PATCH | `/api/v1/notifications/{id}/read` | 标记单条已读 | - | `NotificationResponse` |
| POST | `/api/v1/notifications/read-all` | 全部标记已读 | - | `{ updated_count: int }` |

### 5.3 Schema 定义

```python
# --- 任务相关 ---

class QuestAssignmentResponse(BaseModel):
    id: UUID
    quest_code: str
    quest_type: Literal["daily", "monthly", "special"]
    title_i18n_key: str          # i18n key
    description_i18n_key: str
    target_metric: str
    target_value: int
    progress_value: int
    status: Literal["in_progress", "completed", "claimed", "expired"]
    reward_type: Literal["asset", "item"]
    reward_asset_code: str | None
    reward_quantity: int
    reward_item_code: str | None
    reward_i18n_key: str
    reward_icon: str
    action_i18n_key: str
    action_type: Literal["claim", "navigate", "continue"]
    navigate_to: str | None
    icon: str
    icon_tone: Literal["violet", "green", "blue", "amber"]
    expires_at: datetime | None
    locked: bool

class QuestListResponse(BaseModel):
    daily_quests: list[QuestAssignmentResponse]
    daily_refresh_at: datetime
    monthly_progress: MonthlyProgressResponse
    streak_days: int
    streak_milestone: dict | None

class QuestClaimResponse(BaseModel):
    assignment_id: UUID
    status: Literal["claimed"]
    reward_type: str
    reward_asset_code: str | None
    reward_quantity: int
    reward_item_code: str | None
    coin_balance_after: int | None
    item_quantity_after: int | None

class MonthlyProgressResponse(BaseModel):
    current: int
    target: int
    year_month: str
    days_remaining: int
    completed_day_keys: list[str]

# --- 通知相关 ---

class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str | None
    is_read: bool
    related_quest_id: UUID | None
    action_url: str | None
    created_at: datetime

class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
```

### 5.4 核心业务逻辑

#### 每日任务自动分配与重置

```
用户请求 GET /api/v1/quests 时：
1. 获取用户当前周期的任务
2. 如果今日任务不存在（新的一天），则：
   a. 将昨日 daily 任务标记为 expired
   b. 为用户创建今日 daily 任务（基于 quest 定义 seed）
   c. 触发通知：有新任务可做
3. 刷新今日任务的 progress_value（从 runs/documents 表聚合）
4. 如果 progress_value >= target_value 且 status == in_progress：
   a. 更新 status 为 completed
   b. 触发通知：任务完成可领取奖励
5. 同步更新月度进度
6. 返回完整任务列表
```

#### 领取奖励逻辑

```
POST /api/v1/quests/{assignment_id}/claim 时：
1. 验证 assignment 属于当前用户
2. 验证 status == completed（未完成不能领取）
3. 幂等检查：如果已 claimed，返回当前状态
4. 更新 status 为 claimed
5. 如果 reward_type == asset：
   a. 写入 wallet_ledger（reason_code = "quest_claim"）
6. 如果 reward_type == item：
   a. 写入 inventories 表（quantity += 1）
7. 创建通知：奖励已领取
8. 返回 QuestClaimResponse
```

#### 进度聚合规则

| target_metric | 数据源 | 聚合方式 |
|---------------|--------|---------|
| `document_upload` | `documents` 表 | 今日 `created_at` 的记录数 |
| `streak` | `runs` 表 | 计算连续学习天数 |
| `run_count_endless` | `runs` 表 | 今日 `mode=endless, status=completed` 的记录数 |
| `accuracy_gte_80` | `runs` + `run_answers` | 今日任意一次 run 正确率 ≥ 80% |
| `study_minutes` | `runs` 表 | 今日 `ended_at - started_at` 累计分钟数 |
| `endless_floors` | `runs` 表 | 今日深渊最多到达的层数 |
| `run_count_speed` | `runs` 表 | 今日 `mode=speed, status=completed` 的记录数 |
| `run_count_draft` | `runs` 表 | 今日 `mode=draft, status=completed` 的记录数 |
| `endless_floors_gte_10` | `runs` 表 | 今日深渊到达≥10层的 run |
| `streak_days` | `runs` 表 | 从今天起连续有完成记录的天数 |
| `daily_quests_completed` | `quest_assignments` | 当月 `status IN ('completed','claimed')` 的 daily 任务数 |

---

## 6. 前端交互设计

### 6.1 任务页面加载流程

```
QuestsPage.onMounted()
  ├── API: GET /api/v1/quests
  │     返回: { daily_quests, daily_refresh_at, monthly_progress, streak_days }
  ├── API: GET /api/v1/notifications
  │     返回: { items, unread_count }
  ├── 渲染任务卡片（从 API 数据映射，i18n key 翻译）
  ├── 渲染月度进度条（monthly_progress.current / monthly_progress.target）
  ├── 渲染剩余天数（days_remaining，从 API 获取）
  ├── 渲染刷新倒计时（daily_refresh_at 转本地时间）
  ├── 渲染通知小圆点（unread_count > 0 时显示）
  └── 设置定时器：每分钟刷新倒计时
```

### 6.2 领取奖励流程

```
用户点击「领取奖励」按钮
  ├── 前端验证：status === "completed"
  ├── 弹出确认弹窗（i18n）：是否领取 xxx 奖励？
  │     ├── 取消 → 关闭弹窗
  │     └── 确认 → API: POST /api/v1/quests/{id}/claim
  │           ├── 成功 →
  │           │     更新该任务 status 为 "claimed"
  │           │     若奖励是金币 → 更新顶部金币余额
  │           │     弹出成功 toast（i18n）：奖励已领取！
  │           │     刷新通知列表
  │           └── 失败 → 弹出错误 toast（i18n）
```

### 6.3 上传按钮流程

```
任务卡片 action_type === "navigate" && navigate_to === "/library?action=upload"
  → 点击按钮 → router.push("/library?action=upload")
  → 书库页面检测 URL 参数 → 自动弹出上传弹窗
```

### 6.4 通知弹窗交互

```
点击通知铃铛图标
  ├── API: GET /api/v1/notifications
  ├── 渲染通知列表（title + time，全部 i18n 化）
  ├── 点击通知 → PATCH /api/v1/notifications/{id}/read
  └── 全部已读按钮 → POST /api/v1/notifications/read-all
```

### 6.5 小圆点显示逻辑

```typescript
// 替换当前硬编码的 <span class="notify-btn__dot" />
// 改为：
<span v-if="unreadCount > 0" class="notify-btn__dot" aria-hidden="true" />

// unreadCount 从 GET /api/v1/notifications 的 unread_count 字段获取
```

---

## 7. i18n 策略

### 7.1 原则：后端返回 i18n key，前端翻译

后端**不存储翻译文本**，只存储 i18n key，前端通过 `vue-i18n` 翻译。

```python
# 后端返回示例
{
  "quest_code": "quest-upload",
  "title_i18n_key": "quests.missionUploadTitle",
  "reward_i18n_key": "quests.rewardGoldChest",
  "action_i18n_key": "quests.upload"
}
```

```vue
<!-- 前端渲染 -->
<span>{{ t(task.title_i18n_key) }}</span>
```

### 7.2 通知的 i18n 策略

通知内容需要包含动态参数（如"连胜7天达成！"），后端拼接参数后翻译比前端处理更简单可靠。

```python
# 后端伪代码
async def get_notifications(user_id: UUID, lang: str) -> list[NotificationResponse]:
    notifications = await repo.get_unread(user_id)
    for n in notifications:
        n.title = translate_notification_title(n.type, n.metadata, lang)
        n.body = translate_notification_body(n.type, n.metadata, lang)
    return notifications
```

### 7.3 月份天数计算修复

```typescript
// 修复：剩余天数 = 当月总天数 - 当前日期
const getDaysRemainingInMonth = (): number => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();
  const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
  return totalDaysInMonth - today;
};
```

---

## 8. 错误处理

### 8.1 错误码映射

| 场景 | HTTP 状态码 | 错误码 | 前端处理 |
|------|------------|--------|----------|
| 任务不存在 | 404 | `QUEST_NOT_FOUND` | toast 提示 "任务不存在"，刷新任务列表 |
| 任务未完成就领取 | 409 | `QUEST_NOT_COMPLETED` | toast 提示 "任务尚未完成" |
| 任务已领取过 | 409 | `QUEST_ALREADY_CLAIMED` | 静默更新状态为 claimed |
| 任务已过期 | 410 | `QUEST_EXPIRED` | toast 提示 "任务已过期"，刷新列表 |
| 通知不存在 | 404 | `NOTIFICATION_NOT_FOUND` | 静默忽略，刷新通知列表 |
| 钱包写入失败 | 500 | `REWARD_GRANT_FAILED` | toast 提示 "奖励发放失败" |
| 道具写入失败 | 500 | `ITEM_GRANT_FAILED` | toast 提示 "道具发放失败" |
| 网络超时/断线 | - | `NETWORK_ERROR` | 使用 fallback 数据，显示离线提示 |

### 8.2 重试策略

```typescript
const claimReward = async (assignmentId: string) => {
  const result = await withRetry(() => api.post(`/quests/${assignmentId}/claim`), {
    maxRetries: 3,
    retryOn: [408, 429, 500, 502, 503],
  });
  // 409 (QUEST_ALREADY_CLAIMED) 视为成功
  if (result.status === 409 && result.error_code === "QUEST_ALREADY_CLAIMED") {
    return { status: "claimed" };
  }
  return result;
};
```

---

## 9. 测试策略

### 9.1 后端测试

| 层级 | 测试范围 | 文件 |
|------|---------|------|
| API 测试 | `GET /quests` 返回正确结构 | `tests/api/test_quests_api.py` |
| API 测试 | `POST /quests/{id}/claim` 幂等性 | `tests/api/test_quests_api.py` |
| API 测试 | `GET /notifications` 过滤已读 | `tests/api/test_notifications_api.py` |
| Service 测试 | 每日任务自动创建 | `tests/services/test_quest_service.py` |
| Service 测试 | 进度聚合逻辑（各 target_metric） | `tests/services/test_quest_service.py` |
| Service 测试 | 奖励发放（金币/道具） | `tests/services/test_quest_service.py` |
| Service 测试 | 连胜里程碑检测 | `tests/services/test_quest_service.py` |
| Repository 测试 | CRUD 操作 | `tests/repositories/test_quest_repository.py` |

### 9.2 前端测试

| 层级 | 测试范围 | 文件 |
|------|---------|------|
| 组件测试 | 任务卡片渲染（含 i18n） | `DungeonScholarQuestsPage.spec.ts` |
| 组件测试 | 通知弹窗渲染和数据绑定 | `NotificationPopover.spec.ts` |
| 集成测试 | 领取奖励完整流程 | `DungeonScholarQuestsPage.spec.ts` |
| 集成测试 | 月度进度条更新 | `DungeonScholarQuestsPage.spec.ts` |

---

## 10. 风险与约束

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 任务进度聚合查询可能较慢 | 首次加载延迟 | 缓存策略：任务进度在用户请求时计算并缓存，后续只增量更新 |
| 连胜计算跨时区问题 | 用户看到错误连胜数 | 使用 Asia/Shanghai 时区计算，前端也统一为该时区 |
| 并发领取奖励 | 双领风险 | 使用 idempotency_key + 数据库唯一约束防止重复发放 |
| localStorage 数据迁移 | 旧用户本地数据丢失 | 新系统上线后，前端清除旧 localStorage key，从 API 重新获取 |
| 通知量大 | 表膨胀 | 定期清理90天前的已读通知（后台 job） |
| 月度进度跨月 | 月末/月初边界 | cycle_key 使用 "YYYY-MM" 格式，月末最后一秒过期 |

---

## 11. 验收标准

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 1 | 消息弹窗完全 i18n 化，zh-CN 和 en 均正确显示 | 切换语言验证 |
| 2 | 消息小圆点仅在有未读通知时显示 | API 返回 unread_count > 0 时显示 |
| 3 | 每日任务在自然日交界自动重置 | 修改时区时间验证 |
| 4 | 月度进度条与每日完成同步 | 完成1个日常 → 进度从 X/30 变为 (X+1)/30 |
| 5 | 剩余天数正确计算（如4月3日显示27天） | 断言 `getDaysRemainingInMonth()` |
| 6 | 上传按钮跳转到书库并弹出上传弹窗 | 点击验证 |
| 7 | 领取奖励按钮→后端验证→发放到钱包/道具 | claim API 调用验证 |
| 8 | 时间宝延长翻倍时长的叠加生效 | 使用时间宝后验证翻倍剩余时间增加 |
| 9 | 连胜15天→自动获得时间宝·日 | 触发连胜里程碑验证 |
| 10 | 所有错误场景有正确的 i18n 提示 | 断网/409/410/500 场景测试 |
| 11 | 新用户没有任何历史数据时，任务页面正常展示空状态 | 新注册用户验证 |

---

## 12. 文件结构

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── quests.py          # NEW: 任务 API
│   │   ├── notifications.py   # NEW: 通知 API
│   │   └── router.py          # 更新: 注册新路由
│   ├── services/
│   │   └── quest/
│   │       ├── service.py     # NEW: 任务业务逻辑
│   │       └── schemas.py     # NEW: Quest Pydantic schemas
│   │   └── notification/
│   │       ├── service.py     # NEW: 通知业务逻辑
│   │       └── schemas.py     # NEW: Notification Pydantic schemas
│   ├── repositories/
│   │   ├── quest_repository.py    # NEW
│   │   └── notification_repository.py  # NEW
│   ├── db/models/
│   │   ├── quest.py           # NEW: QuestAssignment 模型
│   │   └── notification.py    # NEW: Notification 模型
│   └── alembic/versions/
│       └── xxxx_add_quest_tables.py  # NEW: 迁移文件
│
frontend/src/
│   ├── api/
│   │   ├── quests.ts          # NEW: 任务 API 调用
│   │   └── notifications.ts   # NEW: 通知 API 调用
│   ├── pages/
│   │   └── DungeonScholarQuestsPage.vue  # 更新: 对接真实 API
│   ├── components/
│   │   ├── NotificationPopover.vue  # 更新: 对接真实 API
│   │   └── ...
│   ├── i18n/
│   │   └── index.ts           # 更新: 新增 quests/i18n 相关翻译
│   └── utils/
│       └── questUtils.ts      # NEW: 任务相关工具函数
│
docs/
├── specs/
│   └── 2026-04-09-quest-system-design.md  # 本文档
└── plans/
    └── 2026-04-09-quest-system-plan.md     # 后续生成
```
