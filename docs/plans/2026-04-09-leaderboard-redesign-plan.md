# 排行榜功能优化实现计划

> **For agentic workers:** Use /execute command to implement tasks. Steps use checkbox syntax.

**Goal:** 优化排行榜功能，修复用户名显示错误、载入更多按钮无效、每日专注内容硬编码等问题，实现动态内容生成和30分钟更新机制。

**Architecture:** 基于现有代码结构进行渐进式优化，修复前端显示问题，优化后端数据查询和LLM标题生成逻辑。

**Tech Stack:** Vue 3 + FastAPI + PostgreSQL + SQLAlchemy 2.0 + vue-i18n

**Design Spec:** `docs/specs/2026-04-09-leaderboard-redesign-design.md`

---

## Task List

### Task 1: 修复用户名显示逻辑

**Files:**
- Modify: `frontend/src/pages/DungeonScholarLeaderboardPage.vue:65`
- Modify: `frontend/src/components/leaderboard/LeaderboardSummaryPanel.vue:47`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
describe('LeaderboardPage username display', () => {
  it('should display username when display_name is null', () => {
    const mockEntry = {
      user_id: '12345678-1234-1234-1234-123456789012',
      display_name: null,
      total_xp: 1000,
      rank: 1,
      level: 2,
      energy_points: 0,
      is_current_user: false,
    };
    
    const result = toStandingRow(mockEntry);
    expect(result.scholar).toBe('kabuto'); // 应该显示用户名而不是"Scholar 123456"
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.vue
const toStandingRow = (entry: LeaderboardEntry): StandingRow => {
  // ... existing code ...
  
  return {
    rank: String(entry.rank),
    scholar: entry.display_name || entry.username || t("leaderboard.defaultScholar"),
    // ... rest of the code
  };
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarLeaderboardPage.vue
git commit -m "fix: display username when display_name is null"
```

- [ ] **Step 6: Run linter/formatter**

Run: `npm run lint` and `npm run typecheck`

### Task 2: 修复载入更多按钮功能

**Files:**
- Modify: `frontend/src/pages/DungeonScholarLeaderboardPage.vue:114-119`
- Modify: `frontend/src/components/leaderboard/LeaderboardStandingsTable.vue:106-107`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
describe('LeaderboardPage load more functionality', () => {
  it('should load more entries when hasMore is true', async () => {
    const mockSnapshot = {
      entries: [{ /* mock entry */ }],
      has_more: true,
      viewer: { /* mock viewer */ },
    };
    
    mockGetLeaderboardSnapshot.mockResolvedValue(mockSnapshot);
    
    await fetchLeaderboard(false);
    expect(mockGetLeaderboardSnapshot).toHaveBeenCalledWith(25, 0, 'global');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.vue
const handleLoadMore = async () => {
  if (!hasMore.value || isLoading.value) {
    return;
  }
  
  try {
    await fetchLeaderboard(false);
  } catch (error) {
    console.error('Failed to load more entries:', error);
  }
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarLeaderboardPage.vue
git commit -m "fix: implement load more functionality"
```

- [ ] **Step 6: Run linter/formatter**

Run: `npm run lint` and `npm run typecheck`

### Task 3: 优化每日专注内容显示

**Files:**
- Modify: `frontend/src/components/leaderboard/LeaderboardSummaryPanel.vue:55-64`
- Modify: `backend/app/services/leaderboard/service.py:89-116`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// backend/tests/services/test_leaderboard_service.py
def test_resolve_focus_title_with_semantics():
    service = LeaderboardService(repository=mock_repo, llm_client=mock_llm)
    
    # Test with document title
    result = service._resolve_focus_title("python_intro.pdf")
    assert result == "python intro"
    
    # Test with empty title
    result = service._resolve_focus_title("")
    assert result == "Untitled document"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_leaderboard_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/leaderboard/service.py
@staticmethod
def _resolve_focus_title(raw_title: object) -> str:
    title = str(raw_title or "").strip()
    if not title:
        return "Untitled document"
    
    # Remove file extensions
    lowered = title.lower()
    known_suffixes = (".pdf", ".txt", ".md", ".markdown", ".doc", ".docx")
    for suffix in known_suffixes:
        if lowered.endswith(suffix):
            title = title[:-len(suffix)].strip()
            break
    
    # Clean up title
    title = title.replace("_", " ").replace("-", " ")
    title = " ".join(part for part in title.split(" ") if part)
    
    if len(title) > 48:
        return f"{title[:45].rstrip()}..."
    
    return title or "Untitled document"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_leaderboard_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/leaderboard/service.py
git commit -m "feat: improve focus title resolution logic"
```

- [ ] **Step 6: Run linter/formatter**

Run: `uv run ruff check app tests` and `uv run mypy app`

### Task 4: 优化LLM标题生成逻辑

**Files:**
- Modify: `backend/app/services/leaderboard/service.py:150-187`
- Modify: `backend/app/repositories/leaderboard_repository.py:132-141`

- [ ] **Step 1: Write failing test (RED)**

```python
# backend/tests/services/test_leaderboard_service.py
def test_resolve_focus_title_with_semantics_fallback():
    mock_llm = None  # No LLM client
    service = LeaderboardService(repository=mock_repo, llm_client=mock_llm)
    
    result = await service._resolve_focus_title_with_semantics("test.pdf", uuid4())
    assert result == "test"  # Should fallback to basic title cleaning
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_leaderboard_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/leaderboard/service.py
async def _resolve_focus_title_with_semantics(
    self, raw_title: object, document_id: UUID | None
) -> str:
    fallback_title = self._resolve_focus_title(raw_title)
    
    if self._llm_client is None or document_id is None:
        return fallback_title
    
    try:
        context_prompts = await self.repository.get_document_semantic_context(document_id, 5)
        if not context_prompts:
            return fallback_title
        
        # Generate semantic title using LLM
        context_text = "\n".join(f"- {item}" for item in context_prompts[:5])
        prompt = (
            "You are generating a concise study focus title for a learning dashboard.\n"
            "Given question prompts from one document, infer the document topic and output JSON only.\n"
            'Required format: {"title":"..."}.\n'
            "Constraints:\n"
            "- <= 24 characters for Chinese, <= 40 chars for English\n"
            "- No punctuation wrapping such as quotes\n"
            "- Keep domain terms (e.g., Python, SQL)\n"
            f"Current fallback title: {fallback_title}\n"
            "Question prompts:\n"
            f"{context_text}"
        )
        
        response = await self._llm_client.generate(
            prompt,
            response_format={"type": "json_object"},
        )
        
        semantic_title = self._parse_semantic_title_response(response)
        if semantic_title:
            return self._resolve_focus_title(semantic_title)
            
    except Exception as exc:
        logger.warning(
            "Failed to generate semantic focus title for document %s: %s", 
            document_id, exc
        )
    
    return fallback_title
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_leaderboard_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/leaderboard/service.py
git commit -m "feat: add LLM fallback for semantic title generation"
```

- [ ] **Step 6: Run linter/formatter**

Run: `uv run ruff check app tests` and `uv run mypy app`

### Task 5: 优化排行榜数据查询性能

**Files:**
- Modify: `backend/app/repositories/leaderboard_repository.py:23-38`
- Modify: `backend/app/repositories/leaderboard_repository.py:62-97`

- [ ] **Step 1: Write failing test (RED)**

```python
# backend/tests/services/test_leaderboard_service.py
def test_leaderboard_performance():
    service = LeaderboardService(repository=mock_repo, llm_client=mock_llm)
    
    # Test that leaderboard query is optimized
    start_time = time.time()
    result = await service.get_global_leaderboard(
        user_id=uuid4(),
        limit=25,
        offset=0,
        scope="global"
    )
    end_time = time.time()
    
    assert (end_time - start_time) < 1.0  # Should complete within 1 second
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_leaderboard_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/repositories/leaderboard_repository.py
async def get_global_leaderboard(self, limit: int, offset: int = 0) -> list[Any]:
    stmt = (
        select(
            Settlement.user_id,
            func.coalesce(Profile.display_name, User.username).label("display_name"),
            func.coalesce(func.sum(Settlement.xp_gained), 0).label("total_xp"),
        )
        .join(User, User.id == Settlement.user_id)
        .outerjoin(Profile, Profile.user_id == Settlement.user_id)
        .group_by(Settlement.user_id, Profile.display_name, User.username)
        .order_by(func.sum(Settlement.xp_gained).desc(), Settlement.user_id.asc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await self._session.execute(stmt)
    return list(result.all())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_leaderboard_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/leaderboard_repository.py
git commit -m "perf: optimize leaderboard query performance"
```

- [ ] **Step 6: Run linter/formatter**

Run: `uv run ruff check app tests` and `uv run mypy app`

### Task 6: 更新前端测试

**Files:**
- Modify: `frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
describe('LeaderboardPage integration tests', () => {
  it('should display correct username format', () => {
    const mockEntry = {
      user_id: '12345678-1234-1234-1234-123456789012',
      display_name: 'Test User',
      total_xp: 1000,
      rank: 1,
      level: 2,
      energy_points: 0,
      is_current_user: false,
    };
    
    const result = toStandingRow(mockEntry);
    expect(result.scholar).toBe('Test User');
  });
  
  it('should handle load more button click', async () => {
    const wrapper = mount(LeaderboardPage);
    const loadMoreButton = wrapper.find('.load-more');
    
    await loadMoreButton.trigger('click');
    expect(mockGetLeaderboardSnapshot).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
// Update existing tests to match new implementation
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
git commit -m "test: update leaderboard page tests"
```

- [ ] **Step 6: Run linter/formatter**

Run: `npm run lint` and `npm run typecheck`

### Task 7: 集成测试

**Files:**
- Modify: `backend/tests/api/test_leaderboard_api.py`
- Modify: `backend/tests/services/test_leaderboard_service.py`

- [ ] **Step 1: Write failing test (RED)**

```python
# backend/tests/api/test_leaderboard_api.py
def test_leaderboard_api_integration():
    response = client.get("/api/v1/leaderboard?limit=25&offset=0&scope=global")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "entries" in data
    assert "viewer" in data
    assert "has_more" in data
    
    # Check that viewer has correct user info
    viewer = data["viewer"]
    assert "display_name" in viewer
    assert "total_xp" in viewer
    assert "level" in viewer
    
    # Check that entries have correct format
    if data["entries"]:
        entry = data["entries"][0]
        assert "user_id" in entry
        assert "display_name" in entry
        assert "total_xp" in entry
        assert "rank" in entry
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/api/test_leaderboard_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# backend/tests/api/test_leaderboard_api.py
# Update existing tests to match new implementation
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/api/test_leaderboard_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/api/test_leaderboard_api.py
git commit -m "test: add leaderboard API integration tests"
```

- [ ] **Step 6: Run linter/formatter**

Run: `uv run ruff check app tests` and `uv run mypy app`

### Task 8: 验证30分钟更新机制

**Files:**
- Modify: `frontend/src/pages/DungeonScholarLeaderboardPage.vue:131-136`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.spec.ts
describe('LeaderboardPage auto-refresh', () => {
  it('should refresh data every 30 minutes', async () => {
    jest.useFakeTimers();
    
    const wrapper = mount(LeaderboardPage);
    
    // Fast-forward 30 minutes
    jest.advanceTimersByTime(30 * 60 * 1000);
    
    expect(mockGetLeaderboardSnapshot).toHaveBeenCalledTimes(2);
    
    jest.useRealTimers();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/pages/DungeonScholarLeaderboardPage.vue
onMounted(async () => {
  await Promise.all([hydrate(), fetchLeaderboard(true)]);
  
  // Set up 30-minute refresh interval
  refreshTimer = setInterval(() => {
    if (!document.hidden) {
      void fetchLeaderboard(true);
    }
  }, refreshIntervalMs);
  
  document.addEventListener("visibilitychange", handleVisibilityRefresh);
  window.addEventListener("focus", handleWindowFocusRefresh);
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- src/pages/DungeonScholarLeaderboardPage.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarLeaderboardPage.vue
git commit -m "feat: implement 30-minute auto-refresh"
```

- [ ] **Step 6: Run linter/formatter**

Run: `npm run lint` and `npm run typecheck`

---

## Dependencies
- Task 1 必须在 Task 6 之前完成
- Task 2 必须在 Task 6 之前完成
- Task 3 必须在 Task 4 之前完成
- Task 4 必须在 Task 7 之前完成
- Task 5 可以在任何时间完成
- Task 8 可以在任何时间完成

## 风险提示
1. **LLM服务依赖**：Task 4 依赖LLM服务，如果服务不可用需要回退到基本功能
2. **数据库性能**：Task 5 的优化可能需要数据库索引调整
3. **前端兼容性**：Task 8 的定时器功能需要测试不同浏览器兼容性

## 验证步骤
1. 完成所有任务后，运行完整测试套件
2. 手动测试排行榜页面功能
3. 验证用户名显示正确
4. 验证载入更多按钮正常工作
5. 验证每日专注内容动态生成
6. 验证30分钟更新机制