# Shops 道具系统设计规格

## 1. 背景与目标

当前商店页只有一个道具（金币包），缺少连胜激冻、经验值翻倍、时间宝、复活币等核心道具，且道具与数据库/后端未联通。本设计旨在：

- 补齐 5 类道具的完整购买→库存→使用→生效链路
- 前端展示与现有金币包风格一致、协调统一
- 后端经济系统闭环：钱包账本 + 库存 + 激活效果 + 使用记录

## 2. 核心使用模型：混合模型

| 道具类型 | 购买行为 | 使用行为 |
|----------|----------|----------|
| 金币包（充值） | 即时到账，增加 COIN 余额，不入库存 | 无 |
| 连胜激冻 | 购买入背包 | 断签时弹窗确认使用 |
| 经验值翻倍（1.5x/2x/3x） | 购买入背包 | 学习/复习开始前或运行中手动使用 |
| 时间宝 | 购买入背包 | 翻倍快到期时弹窗提示使用 |
| 复活币 | 购买入背包 | 无尽深渊失败时优先消耗库存，不足时引导即时购买 |

## 3. 道具效果详细规格

### 3.1 连胜激冻（streak_freeze）

- 触发条件：用户当天未学习，系统判断即将断签
- 弹窗位置：首页/quests 页
- 效果：消耗 1 个道具，延续当天连胜状态
- 不自动使用，需用户确认

### 3.2 经验值翻倍（xp_boost_1_5x / xp_boost_2x / xp_boost_3x）

- 倍率：1.5x / 2x / 3x，每种为独立道具
- 每次使用获得固定时长（如 10 分钟）
- 时长叠加规则：**同倍率可叠加时长**
  - 例：已有 2x 翻倍剩余 10 分钟，再使用一个 2x → 变为 20 分钟
- 不同倍率不共存：当前生效倍率优先，只允许同倍率续时
- 生效范围：library 练习、review 复习、endless-abyss 答题
- 结算时：`实际 XP = 基础 XP × 倍率`

### 3.3 时间宝（time_treasure）

- 仅能对"当前已激活的经验翻倍"延长时长
- 每次使用延长固定时长（如 +10 分钟）
- 无激活中翻倍时不可使用，UI 明确提示
- 触发：翻倍剩余 < 2 分钟时弹窗提示

### 3.4 复活币（revival）

- 仅 endless-abyss 模式可用
- HP 归零时触发复活弹窗：
  - 库存 > 0：主按钮"使用复活币（剩余 x 个）"
  - 库存 = 0：主按钮"购买并使用（xx COIN）"
  - 副按钮始终："放弃，离开深渊"
- 使用效果：
  - 立即恢复 1 HP
  - 获得 3 分钟（180 秒）护盾：下一次答错不扣 HP
  - 护盾只抵消一次错误，消耗后恢复正常扣血
  - 护盾期间再次答错：不扣 HP，但护盾消失
  - 护盾消失后再答错：正常扣 HP

### 3.5 金币包（coin_pack）

- 通过现金购买（真实支付网关为后续集成，本次仅走内部 COIN 闭环）
- 点击后弹出充值弹窗，展示 3-4 个档位
- 每档显示：COIN 数量 / 价格 / 赠送比例 / 推荐标签
- 购买后直接增加 COIN 余额

## 4. 页面结构与组件设计

### 4.1 文件结构

```
frontend/src/
├── pages/
│   └── DungeonScholarShopPage.vue          # 页面外壳
├── components/shop/
│   ├── ShopHeader.vue                      # 品牌 + 钱包 + 背包按钮 + 激活增益胶囊
│   ├── ShopHero.vue                        # 标题 + 筛选标签
│   ├── ShopItemCard.vue                    # 单个商品卡片（通用）
│   ├── ShopItemGrid.vue                    # 卡片网格
│   ├── ShopWalletPill.vue                  # 钱包余额胶囊
│   ├── ShopActiveEffectsBar.vue            # 当前激活增益状态条
│   └── modals/
│       ├── InsufficientBalanceModal.vue    # 余额不足
│       ├── CoinPackTopUpModal.vue          # 金币包充值档位选择
│       ├── ItemUseConfirmModal.vue         # 道具使用确认（通用）
│       ├── TimeTreasurePromptModal.vue     # 翻倍即将到期→时间宝续时
│       └── AbyssReviveModal.vue            # 深渊复活
├── composables/
│   ├── useShopItems.ts                     # 商品列表 + 购买逻辑
│   ├── useInventory.ts                     # 背包库存查询
│   ├── useActiveEffects.ts                 # 激活增益状态 + 倒计时
│   └── useStreakProtection.ts             # 连胜保护判断
└── api/
    └── shop.ts                             # 扩展 use-item / active-effects 接口
```

### 4.2 页面布局（桌面端）

```
┌─────────────────────────────────────────────────────┐
│ ShopHeader: [品牌logo] [钱包pill] [背包btn] [增益条] │
├─────────────────────────────────────────────────────┤
│ ShopHero: 标题 + 描述 + 筛选标签                      │
├─────────────────────────────────────────────────────┤
│ 充值区标题 "代币充值"                                 │
│ [金币包-小额] [金币包-中额⭐] [金币包-大额]             │
├─────────────────────────────────────────────────────┤
│ 道具区标题 "探索道具"                                 │
│ [连胜激冻] [翻倍1.5x] [翻倍2x] [翻倍3x]              │
│ [时间宝] [复活币]                                     │
├─────────────────────────────────────────────────────┤
│ Footer                                                │
└─────────────────────────────────────────────────────┘
```

### 4.3 卡片视觉规范

- 延续现有风格：圆角 18px、浅灰白底 rgba(255,255,255,0.58)、轻阴影、细描边
- 不用 emoji 作为正式图标，改为 SVG 图标（Lucide/Heroicons）
- 通过 accent 色区分品类：
  - 充值：amber
  - 连胜保护：teal
  - 经验翻倍：violet
  - 时间宝：teal
  - 复活币：rose
- 卡片信息层级：
  - 左上：标签（功能型 / 限时增益 / 深渊专属 / 热门）
  - 右上：价格（xx COIN 或 ¥xx）
  - 中部：SVG 图标 + 名称
  - 描述：一句话效果说明
  - 底部：效果摘要 + CTA 按钮

### 4.4 移动端适配

- 卡片从 3 列降为 1 列
- 钱包、背包、激活增益纵向堆叠
- 倒计时状态固定在顶部

## 5. 弹窗状态机

### 5.1 CoinPackTopUpModal

触发：点击金币包卡片
→ 展示档位列表（3-4 档）
→ 用户选档位 → 确认支付
→ POST /api/v1/shop/purchase（offer_id 指向对应档位）
→ 成功：关闭 + toast + 刷新余额
→ 失败：弹窗内展示错误

### 5.2 ItemUseConfirmModal

触发：
- 连胜激冻：首页/quests 判断即将断签
- 经验翻倍：用户在学习页手动点击使用
- 时间宝：翻倍快到期时系统提示

→ 展示道具名称 + 效果说明 + 剩余库存
→ [确认使用] / [取消]
→ POST /api/v1/shop/use-item
→ 成功：关闭 + 执行效果 + 刷新
→ 库存不足：引导去商店购买

### 5.3 TimeTreasurePromptModal

触发：经验翻倍剩余 < 2 分钟
→ 展示当前翻倍倍率 + 剩余时间 + 时间宝库存
→ [使用时间宝] / [前往商店] / [让它到期]

### 5.4 AbyssReviveModal

触发：endless-abyss HP=0 → run status=aborted
→ 检查背包复活币库存
→ 库存 > 0：主按钮"使用复活币（剩余 x 个）"
→ 库存 = 0：主按钮"购买并使用（xx COIN）"
→ COIN 不足：引导充值
→ 副按钮："放弃，离开深渊"

## 6. 后端接口设计

### 6.1 新增端点

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/v1/shop/use-item` | 使用道具 |
| GET | `/api/v1/shop/active-effects` | 查询当前激活效果 |

### 6.2 改造端点

| 方法 | 路径 | 改造内容 |
|------|------|----------|
| POST | `/api/v1/runs/{id}/revive` | 优先消耗库存复活币，护盾时长改 180s |

### 6.3 Use-Item 请求/响应

```python
class UseItemRequest(BaseModel):
    item_code: str  # streak_freeze | xp_boost_1_5x | xp_boost_2x | xp_boost_3x | time_treasure | revival
    context: dict | None = None  # 如 {"run_id": "xxx"}

class UseItemResponse(BaseModel):
    success: bool
    item_code: str
    quantity_remaining: int
    effect_applied: dict | None  # {"type": "xp_boost", "multiplier": 2.0, "expires_at": "..."}
```

### 6.4 Active-Effects 响应

```python
class ActiveEffect(BaseModel):
    id: UUID
    effect_type: str  # xp_boost | revive_shield | streak_freeze
    multiplier: float | None
    expires_at: datetime | None
    source_item_code: str

class ActiveEffectsResponse(BaseModel):
    effects: list[ActiveEffect]
```

## 7. 数据库扩展

### 7.1 新增表 active_effects

```sql
CREATE TABLE active_effects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    effect_type VARCHAR(40) NOT NULL,
    multiplier DECIMAL(5,2),
    expires_at TIMESTAMPTZ,
    source_item_code VARCHAR(80),
    source_use_id UUID,
    context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_active_effects_user_expires ON active_effects(user_id, expires_at);
CREATE INDEX ix_active_effects_user_type ON active_effects(user_id, effect_type);
```

### 7.2 新增表 use_records

```sql
CREATE TABLE use_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_code VARCHAR(80) NOT NULL,
    inventory_id UUID REFERENCES inventories(id),
    effect_snapshot JSONB,
    context JSONB,
    used_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_use_records_user ON use_records(user_id, used_at);
```

### 7.3 shop_offers 的 item_code 统一

| item_code | display_name | ItemType | rarity |
|-----------|-------------|----------|--------|
| coin_pack_small | 金币包·小 | coin_pack | common |
| coin_pack_medium | 金币包·中 | coin_pack | uncommon |
| coin_pack_large | 金币包·大 | coin_pack | legendary |
| streak_freeze | 连胜激冻 | streak_freeze | common |
| xp_boost_1_5x | 经验翻倍·1.5x | xp_boost | uncommon |
| xp_boost_2x | 经验翻倍·2x | xp_boost | rare |
| xp_boost_3x | 经验翻倍·3x | xp_boost | legendary |
| time_treasure | 时间宝 | time_treasure | uncommon |
| revival | 复活币 | revival | rare |

### 7.4 ItemType 枚举扩展

在现有 `coin_pack | streak_freeze | time_treasure | revival` 基础上新增 `xp_boost`。

## 8. 核心业务逻辑

### 8.1 经验翻倍生效

生效点：`backend/app/services/runs/service.py` 的 `_build_settlement()`

```
现有：_calculate_score() → settlement.xp_gained → wallet credit XP
改造：_calculate_score() → 查询 active_effects(xp_boost)
      → 有激活中的 xp_boost：xp_gained *= multiplier
      → settlement.xp_gained = 翻倍后值
      → wallet credit XP
```

### 8.2 复活币改造

```
现有：RunService.revive() 直接扣 10 COIN
改造：
  1. 查 inventory 中 revival 数量
  2. > 0：消耗 1 个，不走 purchase
  3. = 0：走现有扣币逻辑（或引导购买）
  4. 恢复 1 HP + 180s 护盾（现有 60s 改为 180s）
```

### 8.3 连胜激冻生效

```
用户确认使用 → 后端标记当天 streak 已保护
→ 前端首页/quests streak 状态不中断
```

### 8.4 时间宝生效

```
检查当前 active_effects 中有无 xp_boost
→ 有：延长 expires_at（+固定时长如 600s）
→ 无：返回错误"当前无激活中的经验翻倍"
```

## 9. 错误处理

| 场景 | HTTP 状态 | 错误码 | 说明 |
|------|-----------|--------|------|
| 库存不足 | 400 | INSUFFICIENT_INVENTORY | item 库存为 0 |
| 无激活中翻倍 | 400 | NO_ACTIVE_BOOST | 时间宝使用时无翻倍 |
| 道具不可用 | 400 | ITEM_NOT_USABLE | 非法 item_code |
| 余额不足 | 400 | INSUFFICIENT_BALANCE | 购买时 COIN 不够 |
| Offer 不存在 | 404 | OFFER_NOT_FOUND | offer_id 无效 |
| 限购超出 | 400 | PURCHASE_LIMIT_EXCEEDED | 超过每人限购 |
| 非深渊模式使用复活币 | 400 | INVALID_CONTEXT | context 缺少 run_id |

## 10. 测试策略

### 后端

- 单元测试：ShopService.use_item() 各道具分支
- 单元测试：RunService._build_settlement() 翻倍生效
- 单元测试：RunService.revive() 库存优先消耗
- API 测试：POST /use-item 各场景
- API 测试：GET /active-effects
- 集成测试：购买 → 入库 → 使用 → 激活效果 → 结算翻倍

### 前端

- 组件测试：ShopItemCard 渲染与交互
- 组件测试：CoinPackTopUpModal 档位选择
- 组件测试：AbyssReviveModal 库存判断
- 页面测试：ShopPage 完整购买流程
- composable 测试：useActiveEffects 倒计时与过期
- E2E：充值 → 购买道具 → 使用 → 验证效果

## 11. 风险与约束

1. **真实支付未对接**：金币包充值弹窗本次仅走 COIN 内部闭环，真实支付网关为后续集成
2. **XP 翻倍叠加**：首版只支持同倍率续时，不允许不同倍率共存
3. **护盾时长**：从 60s 改为 180s，需确认不影响 speed-survival 等其他模式
4. **连胜激冻判断**：依赖现有 streak 数据，需与首页打卡逻辑对齐
5. **库存上限**：建议每种道具设置 max_capacity，避免囤积

## 12. 验收标准

| 编号 | 验收项 | 验证方式 |
|------|--------|----------|
| A1 | 商店页展示 3 个充值档位金币包卡片，点击进入充值弹窗 | 前端 E2E |
| A2 | 购买金币包后 COIN 余额即时增加，不入库存 | API 测试 |
| A3 | 商店页展示连胜激冻、3 种经验翻倍、时间宝、复活币卡片 | 前端测试 |
| A4 | 购买道具后进入背包（inventory），数量正确 | API 测试 |
| A5 | 使用连胜激冻后当天连胜不断 | 集成测试 |
| A6 | 使用经验翻倍后，run 结算 XP 乘以对应倍率 | 后端单元测试 |
| A7 | 同倍率经验翻倍时长可叠加 | 后端测试 |
| A8 | 翻倍快到期时前端弹窗提示时间宝 | 前端测试 |
| A9 | 使用时间宝后延长当前翻倍时长 | API 测试 |
| A10 | endless-abyss HP=0 时弹窗，优先消耗背包复活币 | 前端 + API 测试 |
| A11 | 复活后获得 1HP + 3 分钟护盾，护盾抵消一次错误 | 后端测试 |
| A12 | 库存不足时弹窗引导购买，余额不足时引导充值 | 前端测试 |
| A13 | 背包入口可查看所有已购买道具及数量 | 前端测试 |
| A14 | 激活增益状态条正确展示当前翻倍倍率和倒计时 | 前端测试 |
| A15 | 移动端布局正常（1 列卡片、状态条纵向堆叠） | 视觉验收 |
| A16 | 后端 ruff + mypy 通过 | CI |
| A17 | 前端 lint + typecheck + 测试通过 | CI |
