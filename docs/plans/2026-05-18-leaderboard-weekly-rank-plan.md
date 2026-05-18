# 排行榜周榜与段位改版实施计划

## 总览

本次改版采用最小可上线方案：后端继续复用 `GET /api/v1/leaderboard`，按北京时间周窗口实时聚合 `Settlement.xp_gained` 作为本周经验，并扩展段位、晋级区、周窗口字段；前端移除等级与幽火分展示，改为展示“当前排名 · 段位”“本周经验”和动态周榜倒计时。

不新增数据库表，不实现跨周自动结算和持久化段位。当前所有用户默认段位为 `见习学徒`，前五名标记为 `晋级区`。

## 前置准备

- [ ] 确认设计文档 `docs/designs/2026-05-18-leaderboard-weekly-rank-design.md` 已批准。
- [ ] 检查前端端口 `5173`、后端端口 `8000` 是否被占用；若占用，先停止服务。
- [ ] 运行现有基线测试：
  - 后端：`uv run python -m pytest tests/api/test_leaderboard_api.py tests/services/test_leaderboard_service.py -q`
  - 前端：`npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`

## 任务列表

### 任务 1: 扩展后端排行榜响应 Schema

- 修改 `backend/app/schemas/leaderboard.py`
- 增加 `weekly_xp`、`tier_key`、`tier_name`、`is_promotion_zone`
- 列表响应增加 `week_starts_at`、`week_ends_at`、`promotion_cutoff_rank`

### 任务 2: 为北京时间周窗口添加服务层单元测试

- 修改 `backend/tests/services/test_leaderboard_service.py`
- 覆盖北京时间周一和周日边界

### 任务 3: 实现北京时间周窗口工具方法

- 修改 `backend/app/services/leaderboard/service.py`
- 使用 `Asia/Shanghai` 计算周一 00:00 到下周一 00:00

### 任务 4: 添加仓储层周榜查询方法

- 修改 `backend/app/repositories/leaderboard_repository.py`
- 修改 `backend/app/services/leaderboard/service.py` 协议
- 新增周榜、周榜人数、用户周经验、用户周排名查询

### 任务 5: 编写服务层周经验与晋级区测试

- 修改 `backend/tests/services/test_leaderboard_service.py`
- 覆盖 `weekly_xp`、默认段位、前五晋级区

### 任务 6: 实现服务层周榜快照组装

- 修改 `backend/app/services/leaderboard/service.py`
- 使用周榜查询填充新增字段
- 保留 `total_xp`，最小版本中与 `weekly_xp` 一致

### 任务 7: 更新后端 API 测试字段

- 修改 `backend/tests/api/test_leaderboard_api.py`
- 覆盖新增字段序列化

### 任务 8: 后端质量验证

- `uv run ruff check app tests`
- `uv run mypy app`
- `uv run python -m pytest tests/api/test_leaderboard_api.py tests/services/test_leaderboard_service.py -q`

### 任务 9: 扩展前端排行榜 API 类型

- 修改 `frontend/src/api/leaderboard.ts`
- 增加周榜字段，可选兼容旧后端

### 任务 10: 添加前端周榜倒计时工具测试

- 新建 `frontend/src/utils/leaderboardWeek.spec.ts`
- 覆盖周一 6 天、周日今天结束、无后端结束时间 fallback

### 任务 11: 实现前端周榜倒计时工具

- 新建 `frontend/src/utils/leaderboardWeek.ts`
- 计算北京时间周结束时间和倒计时文案参数

### 任务 12: 改造左侧排行榜个人卡片

- 修改 `frontend/src/components/leaderboard/LeaderboardSummaryPanel.vue`
- 移除等级和幽火分
- 展示“当前排名 · 段位”“本周经验”“前 5 名晋级下一段位”

### 任务 13: 改造右侧排行榜表格状态与副标题

- 修改 `frontend/src/components/leaderboard/LeaderboardStandingsTable.vue`
- 移除降级区/危险区
- 副标题支持动态倒计时
- 前五显示晋级区

### 任务 14: 页面层接入周榜字段和降级兼容

- 修改 `frontend/src/pages/DungeonScholarLeaderboardPage.vue`
- 使用 `weekly_xp ?? total_xp`
- 默认段位 `见习学徒`
- fallback 晋级区为 `rank <= promotion_cutoff_rank`

### 任务 15: 更新排行榜 i18n 文案

- 修改 `frontend/src/i18n/index.ts`
- 新增“本周经验”“晋级区”“本周竞赛将在 {days} 天后结束”等文案
- 删除等级/幽火分语义

### 任务 16: 更新前端页面测试

- 修改 `frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts`
- 覆盖新标题、本周经验、晋级区、不显示等级/幽火分

### 任务 17: 前端质量验证

- `npm run lint`
- `npm run typecheck`
- `npm run test -- src/utils/leaderboardWeek.spec.ts src/pages/DungeonScholarLeaderboardPage.spec.ts`

### 任务 18: 全链路回归验证

- 后端目标验证全部通过
- 前端目标验证全部通过
- `GET /api/v1/leaderboard` 响应包含周榜字段
- 前端排行榜不再显示等级和幽火分

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| `Settlement` 时间字段与假设不一致 | 实现前确认模型字段 |
| 北京时间周窗口错误 | 加周一/周日边界测试 |
| 旧前端依赖 `total_xp` | 保留 `total_xp` 并与 `weekly_xp` 对齐 |
| 暂无持久化段位 | 使用 `tier_key` 预留后续替换 |

## 最终验收标准

- 后端排行榜按北京时间本周窗口统计 `Settlement.xp_gained`。
- 接口返回 `week_starts_at`、`week_ends_at`、`weekly_xp`、`tier_key`、`tier_name`、`promotion_cutoff_rank`、`is_promotion_zone`。
- 前端左侧卡片显示“当前排名 · 段位”和“本周经验”。
- 前端不再显示等级和幽火分卡片。
- 右侧排行榜显示动态周榜倒计时。
- 前五名显示 `晋级区`，不再显示降级区/危险区。
