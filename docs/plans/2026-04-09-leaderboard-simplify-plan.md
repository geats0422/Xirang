# 排行榜功能简化实现计划

> **For agentic workers:** Use /execute command to implement tasks. Steps use checkbox syntax.

**Goal:** 移除前端好友/全服切换按钮，简化排行榜UI，只保留全服排行榜功能。

**Architecture:** 移除前端scope切换UI，简化后端处理逻辑，始终返回全服数据。

**Tech Stack:** Vue 3 + FastAPI + PostgreSQL + vue-i18n

**Design Spec:** `docs/specs/2026-04-09-leaderboard-simplify-design.md`

---

## Task List

### Task 1: 移除 LeaderboardStandingsTable 中的 scope 切换按钮

**Files:**
- Modify: `frontend/src/components/leaderboard/LeaderboardStandingsTable.vue`
- Modify: `frontend/src/pages/DungeonScholarLeaderboardPage.vue`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
describe('LeaderboardPage without scope switch', () => {
  it('should not display scope switch buttons', async () => {
    const router = createTestRouter();
    await router.push(ROUTES.leaderboard);
    await router.isReady();

    const wrapper = mount(DungeonScholarLeaderboardPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.findAll('.scope-btn')).toHaveLength(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```vue
<!-- LeaderboardStandingsTable.vue - 移除 scope 切换按钮 -->
<!-- 删除 switches 部分的按钮 -->

<!-- 修改后的 board-header -->
<header class="board-header">
  <div>
    <h2>{{ t("leaderboard.table.title") }}</h2>
    <p>{{ t("leaderboard.table.subtitle") }}</p>
  </div>
  <!-- 移除 switches 部分的按钮 -->
</header>
```

```typescript
// LeaderboardStandingsTable.vue - 移除 props
defineProps<{
  statusClass: (row: StandingRow) => string;
  standings: StandingRow[];
  hasMore: boolean;
  isLoading: boolean;
}>();

// 移除 scopeChange 事件
const emit = defineEmits<{
  loadMore: [];
}>();
```

```typescript
// DungeonScholarLeaderboardPage.vue - 移除 scope 状态和事件处理
// 移除 scope 相关代码
const scope = ref<"global" | "friends">("global");
const handleScopeChange = async (nextScope: "global" | "friends") => {
  scope.value = nextScope;
  await fetchLeaderboard(true);
};

// 修改 fetchLeaderboard 调用，不传递 scope
const snapshot = await getLeaderboardSnapshot(pageSize, offset);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/leaderboard/LeaderboardStandingsTable.vue
git add frontend/src/pages/DungeonScholarLeaderboardPage.vue
git commit -m "feat: remove scope switch buttons from leaderboard"
```

- [ ] **Step 6: Run linter/formatter**

Run: `npm run lint` and `npm run typecheck`

### Task 2: 更新 LeaderboardStandingsTable 组件的 props

**Files:**
- Modify: `frontend/src/components/leaderboard/LeaderboardStandingsTable.vue`

- [ ] **Step 1: 检查现有实现**

确认 LeaderboardStandingsTable 的 props 定义需要更新

- [ ] **Step 2: 更新组件 props**

```typescript
// LeaderboardStandingsTable.vue
defineProps<{
  statusClass: (row: StandingRow) => string;
  standings: StandingRow[];
  hasMore: boolean;
  isLoading: boolean;
}>();
```

- [ ] **Step 3: 更新模板中事件绑定**

移除 `@scope-change` 绑定，只保留 `@load-more`

- [ ] **Step 4: 运行测试验证**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/leaderboard/LeaderboardStandingsTable.vue
git commit -m "refactor: update LeaderboardStandingsTable props"
```

### Task 3: 更新前端 API 调用

**Files:**
- Modify: `frontend/src/api/leaderboard.ts`

- [ ] **Step 1: 更新 API 函数签名**

```typescript
// frontend/src/api/leaderboard.ts
export const getLeaderboardSnapshot = async (
  limit = 25,
  offset = 0,
): Promise<LeaderboardSnapshot> => {
  return apiRequest<LeaderboardSnapshot>(
    `/api/v1/leaderboard?limit=${limit}&offset=${offset}`,
  );
};
```

- [ ] **Step 2: 运行测试验证**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/leaderboard.ts
git commit -m "refactor: simplify getLeaderboardSnapshot API"
```

### Task 4: 更新前端测试

**Files:**
- Modify: `frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts`

- [ ] **Step 1: 移除 scope 相关测试**

```typescript
// 移除以下测试用例：
// - "resets pagination when switching scope"
// - 任何涉及 scope="friends" 的测试
```

- [ ] **Step 2: 运行测试验证**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: 剩余测试全部通过

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
git commit -m "test: remove scope-related tests"
```

### Task 5: 后端 API 添加日志（可选）

**Files:**
- Modify: `backend/app/api/v1/leaderboard.py`
- Modify: `backend/app/services/leaderboard/service.py`

- [ ] **Step 1: 在后端添加日志记录**

```python
# backend/app/api/v1/leaderboard.py
@router.get("", response_model=LeaderboardListResponse)
async def list_leaderboard(
    limit: int = 25,
    offset: int = 0,
    scope: str = "global",
    user_id: UUID = Depends(get_current_user_id),
    service: LeaderboardService = Depends(get_leaderboard_service),
) -> LeaderboardListResponse:
    logger.info(f"Leaderboard request: scope={scope}, limit={limit}, offset={offset}")
    return await service.get_global_leaderboard(
        user_id=user_id,
        limit=limit,
        offset=offset,
        scope=scope,
    )
```

- [ ] **Step 2: 运行后端测试验证**

Run: `uv run pytest tests/api/test_leaderboard_api.py -v`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/leaderboard.py
git commit -m "chore: add logging for scope parameter"
```

---

## Dependencies
- Task 1 必须在 Task 2 之前完成
- Task 2 必须在 Task 3 之前完成
- Task 4 必须在 Task 5 之前完成

## 风险提示
1. **UI变更**：移除 scope 切换按钮是UI变更，用户需要适应
2. **后续扩展**：后续添加好友功能时需要重新添加scope UI

## 验证步骤
1. 完成所有任务后，运行完整测试套件
2. 手动测试排行榜页面功能
3. 验证 scope 切换按钮已移除
4. 验证排行榜始终显示全服数据
5. 验证载入更多按钮正常工作