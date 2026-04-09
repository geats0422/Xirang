# 游戏结算与答题流程优化设计规格

## 1. 背景与目标

### 问题描述
1. **Speed-Survival 和 Knowledge Draft 答题错误后流程卡死**：用户答错后显示解析，但无法继续答题或直接进入下一题
2. **结算弹窗数据不完整**：修行目标应显示今日目标，且数据来源应独立于 run settlement
3. **硬编码 I18n**：ShopHeader.vue 中品牌名"息壤"硬编码未国际化

### 目标
- 修复 Speed-Survival 答题错误后流程，用户可点击正确答案继续下一题
- 修复 Knowledge Draft 答题错误后流程，同样的交互逻辑
- 结算弹窗接入真实今日目标数据（从独立 API 获取）
- 修复 ShopHeader.vue 硬编码的国际化问题

---

## 2. 技术方案

### 方案选择
**最小改动 + 职责分离**

- Bug 修复优先，避免引入新的复杂性
- 今日目标数据独立获取，解耦 run 生命周期
- I18n 修复使用现有 i18n key 规范

### 核心改动

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `DungeonScholarSpeedSurvivalPage.vue` | Bug 修复 | 答错后显示解析，用户点击正确答案进入下一题 |
| `DungeonScholarKnowledgeDraftPage.vue` | Bug 修复 | 同上，适配 Knowledge Draft 的交互逻辑 |
| `GameSettlementModal.vue` | 数据获取 | 从 props 接收今日目标，支持从独立 API 获取 |
| `ShopHeader.vue` | I18n 修复 | 将硬编码中文替换为 i18n key |

---

## 3. 架构设计

### 3.1 Speed-Survival 答题流程

```
用户选择答案
    ↓
submitAnswer API
    ↓
┌─────────────────────────────────┐
│  is_correct = true?             │
├───────────────┬─────────────────┤
│   Yes         │   No            │
│   ↓           │   ↓             │
│   combo++     │   combo = 0     │
│   显示下一题   │   显示解析      │
│               │   + 正确答案     │
│               │   ↓             │
│               │ 用户点击正确    │
│               │  选项          │
│               │   ↓             │
│               │ 进入下一题     │
└───────────────┴─────────────────┘
```

### 3.2 Knowledge Draft 答题流程

```
用户填空并提交
    ↓
submitAnswer API
    ↓
┌─────────────────────────────────┐
│  is_correct = true?             │
├───────────────┬─────────────────┤
│   Yes         │   No            │
│   ↓           │   ↓             │
│   显示下一题   │   显示解析      │
│               │   + 正确答案    │
│               │   ↓             │
│               │ awaiting_       │
│               │ correction=true  │
│               │   ↓             │
│               │ 用户点击正确    │
│               │ 选项           │
│               │   ↓             │
│               │ 进入下一题     │
└───────────────┴─────────────────┘
```

### 3.3 结算弹窗数据流

```
GameSettlementModal 打开
    ↓
父组件调用 GET /api/v1/user/daily-goal
    ↓
获取今日目标进度 (goalCurrent, goalTotal)
    ↓
传入 settlementGoalCurrent, settlementGoalTotal
    ↓
显示结算弹窗
```

---

## 4. 接口设计

### 4.1 新增 API

#### GET /api/v1/user/daily-goal

获取用户今日学习目标进度。

**技术实现方案**:

后端复用现有的 `runs` 表数据，按日期聚合计算用户今日学习时长。

**Response Schema** (`app/schemas/user.py`):
```python
class DailyGoalResponse(BaseModel):
    goal_current: int = 0  # 今日已完成的学习分钟数
    goal_total: int = 60   # 每日目标分钟数（固定值）
    goal_unit: str = "minutes"
    is_completed: bool = False
    streak_days: int = 0   # 连续学习天数
```

**数据来源**:
- `goal_current`: 从 `runs` 表查询今日完成的 runs，计算 `SUM(ended_at - started_at)` 得到总学习时长（分钟）
- `goal_total`: 固定 60 分钟（可在 `UserSetting` 中扩展为用户可配置）
- `streak_days`: 需要查询历史记录计算连续学习天数，或复用 `UserSetting.streak_days`

**实现位置**:

| 层级 | 文件 | 说明 |
|------|------|------|
| Schema | `app/schemas/user.py` | 新增 `DailyGoalResponse` |
| Repository | `app/repositories/user_repository.py` | 新增 `get_daily_goal()` 方法 |
| Service | `app/services/user/service.py` | 新增 `get_daily_goal()` 方法 |
| API Route | `app/api/v1/user.py` | 新增 `GET /daily-goal` 路由 |

**Response**:
```json
{
  "goal_current": 25,
  "goal_total": 60,
  "goal_unit": "minutes",
  "is_completed": false,
  "streak_days": 7
}
```

**错误处理**:
- 用户无任何 run 记录：返回 `goal_current=0, streak_days=0`
- 数据库错误：返回 HTTP 500

### 4.2 现有 API 变更

无变更。API 响应格式保持不变。

---

## 5. 详细改动说明

### 5.1 Speed-Survival Bug 修复

**文件**: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`

**当前问题代码** (约第 231-248 行):
```typescript
} else {
  combo.value = 0;
  runStatus.value = "normal";
  showFeedback.value = true;
  isSubmittingAnswer.value = false;
  if (result.settlement) {
    // 显示结算弹窗
    showSettlement.value = true;
    stopTicker();
    return;  // ❌ 直接返回，不允许用户继续
  }
  return;
}
```

**修复逻辑**:
1. 答错后不检查 `result.settlement`，直接显示解析
2. 用户点击正确答案选项时，清除 `showFeedback` 并继续下一题
3. `showFeedback` 状态下，用户仍可点击选项，但再次答错不会重复显示解析

### 5.2 Knowledge Draft Bug 修复

**文件**: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`

**当前问题代码** (约第 528-537 行):
```typescript
if (!result.is_correct) {
  showNotice.value = true;
  showFeedback.value = true;
  awaitingCorrection.value = true;  // ❌ 这个状态要求用户填写正确组合
  expectedCorrectOptionIds.value = resolveExpectedCorrectOptionIds({...});
  return;
}
```

**修复逻辑**:
1. 答错后设置 `awaitingCorrection = true` 显示解析
2. 但在 `awaitingCorrection = true` 状态下，用户点击**任意选项**都直接进入下一题
3. 不再要求用户填写完整的正确组合

### 5.3 结算弹窗数据修复

**文件**: `frontend/src/components/GameSettlementModal.vue`
**父组件**: 各游戏模式页面

**改动**:
1. 父组件在打开结算弹窗前，调用 `GET /api/v1/user/daily-goal` 获取今日目标
2. 将 `goalCurrent` 和 `goalTotal` 传入 `GameSettlementModal`
3. 移除或保留原有的 `goalText` 作为 fallback

### 5.4 ShopHeader I18n 修复

**文件**: `frontend/src/components/shop/ShopHeader.vue`

**品牌名国际化规范**:
- 中文（简体/繁体）：显示"息壤"
- 其他语言：显示"Xi Rang"

**当前代码**:
```vue
<strong>息壤</strong>
<button aria-label="背包">
```

**修复后**:
```vue
<strong>{{ $t("shop.brand") }}</strong>
<button :aria-label="$t('shop.bagAria')">
```

**更新 i18n keys**:

英文 (en):
```json
{
  "shop": {
    "brand": "Xi Rang",
    "bagAria": "Bag"
  }
}
```

中文简体 (zh-CN):
```json
{
  "shop": {
    "brand": "息壤",
    "bagAria": "背包"
  }
}
```

中文繁体 (zh-TW):
```json
{
  "shop": {
    "brand": "息壤",
    "bagAria": "背包"
  }
}
```

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|----------|
| `GET /api/v1/user/daily-goal` 失败 | 使用 fallback 值 `goalCurrent=0, goalTotal=8` |
| Speed-Survival 解析状态下超时 | 保持解析显示，允许用户继续操作 |
| Knowledge Draft awaitingCorrection 状态下网络错误 | 显示错误提示，用户可重试 |

---

## 7. 验收标准

### Bug 修复验收

1. **Speed-Survival**:
   - [ ] 用户答错后显示解析（包含正确答案和解释）
   - [ ] 用户点击正确答案选项后进入下一题
   - [ ] 不再直接显示结算弹窗

2. **Knowledge Draft**:
   - [ ] 用户答错后显示解析
   - [ ] 用户点击正确答案后进入下一题（无需填写完整组合）

3. **结算弹窗**:
   - [ ] 今日目标显示真实数据
   - [ ] API 失败时有 fallback 值

### 后端 API 验收

4. **GET /api/v1/user/daily-goal**:
   - [ ] 返回今日学习分钟数 `goal_current`
   - [ ] 返回每日目标分钟数 `goal_total`（固定 60）
   - [ ] 返回 `is_completed` 标识是否完成目标
   - [ ] 返回 `streak_days` 连续学习天数
   - [ ] 无数据时返回正确的默认值

4. **I18n**:
   - [ ] ShopHeader 品牌名：中文（简/繁）显示"息壤"，其他语言显示"Xi Rang"
   - [ ] 背包按钮 aria-label 正确国际化

---

## 8. 风险与约束

### 风险
1. **API 依赖**：新增的 `daily-goal` API 需要后端配合实现
2. **状态管理**：修复过程中需小心处理 `showFeedback` 和 `awaitingCorrection` 状态的切换

### 约束
1. 不改变现有的 i18n key 命名规范
2. 不引入新的 API 依赖（复用现有 submitAnswer 响应格式）
3. 保持与现有 UI 样式一致

---

## 9. 测试策略

### 后端单元测试
- `tests/services/test_user_service.py`: 测试 `get_daily_goal()` 方法
- `tests/api/test_user_api.py`: 测试 `GET /api/v1/user/daily-goal` 路由
- 覆盖：无数据、有数据、数据库错误场景

### 前端单元测试
- `DungeonScholarSpeedSurvivalPage`: 测试答错后状态转换
- `DungeonScholarKnowledgeDraftPage`: 测试 awaitingCorrection 逻辑
- `GameSettlementModal`: 测试 fallback 值处理

### E2E 测试
- Speed-Survival 完整答题流程（答错 → 看解析 → 答对 → 下一题）
- Knowledge Draft 完整答题流程
- 结算弹窗数据展示
