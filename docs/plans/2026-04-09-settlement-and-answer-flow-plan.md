# 游戏结算与答题流程优化实现计划

**Goal:** 修复 Speed-Survival 和 Knowledge Draft 答题错误后流程卡死 bug，结算弹窗接入真实今日目标数据，修复 ShopHeader I18n 硬编码问题。

**Architecture:** 
- 后端新增 `/api/v1/user/daily-goal` API 独立提供今日目标数据
- 前端修复两个游戏页面的答题流程状态机逻辑
- I18n 使用 vue-i18n 的 locale 切换机制

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (后端), Vue 3 + TypeScript + Vitest (前端)

**Design Spec:** `docs/specs/2026-04-09-settlement-and-answer-flow-design.md`

---

## Task List

### Phase 1: 后端 API 实现

---

### Task 1: 创建 DailyGoalResponse Schema

**Files:**
- Create: `backend/app/schemas/user.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/schemas/test_user_schemas.py
import pytest
from app.schemas.user import DailyGoalResponse


def test_daily_goal_response_defaults():
    response = DailyGoalResponse()
    assert response.goal_current == 0
    assert response.goal_total == 60
    assert response.goal_unit == "minutes"
    assert response.is_completed is False
    assert response.streak_days == 0


def test_daily_goal_response_with_values():
    response = DailyGoalResponse(
        goal_current=30,
        goal_total=60,
        goal_unit="minutes",
        is_completed=False,
        streak_days=7,
    )
    assert response.goal_current == 30
    assert response.goal_total == 60
    assert response.is_completed is False
    assert response.streak_days == 7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/schemas/test_user_schemas.py -v`
Expected: FAIL (file not found)

- [ ] **Step 3: Write schema**

```python
# backend/app/schemas/user.py
from pydantic import BaseModel


class DailyGoalResponse(BaseModel):
    goal_current: int = 0
    goal_total: int = 60
    goal_unit: str = "minutes"
    is_completed: bool = False
    streak_days: int = 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/schemas/test_user_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/user.py tests/schemas/test_user_schemas.py
git commit -m "feat: add DailyGoalResponse schema"
```

---

### Task 2: 创建 UserRepository.get_daily_goal()

**Files:**
- Create: `backend/app/repositories/user_repository.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/repositories/test_user_repository.py
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.repositories.user_repository import UserRepository


@pytest.fixture
def repository(session):
    return UserRepository(session)


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.mark.asyncio
async def test_get_daily_goal_no_runs(repository, sample_user_id):
    result = await repository.get_daily_goal(sample_user_id)
    assert result.goal_current == 0
    assert result.goal_total == 60
    assert result.streak_days == 0
    assert result.is_completed is False


@pytest.mark.asyncio
async def test_get_daily_goal_with_completed_runs(repository, sample_user_id, session):
    # Create a completed run for today
    from app.db.models.runs import Run, RunStatus, RunMode
    run = Run(
        id=uuid4(),
        user_id=sample_user_id,
        mode=RunMode.SPEED,
        status=RunStatus.COMPLETED,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        ended_at=datetime.now(timezone.utc),
    )
    session.add(run)
    await session.commit()
    
    result = await repository.get_daily_goal(sample_user_id)
    assert result.goal_current >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/repositories/test_user_repository.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write repository**

```python
# backend/app/repositories/user_repository.py
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.runs import Run, RunStatus
from app.schemas.user import DailyGoalResponse


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_daily_goal(self, user_id: UUID) -> DailyGoalResponse:
        tz = timezone(timedelta(hours=8))
        now_local = datetime.now(tz)
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        stmt = (
            select(
                func.count(Run.id).label("run_count"),
                func.coalesce(
                    func.sum(
                        func.extract("epoch", Run.ended_at - Run.started_at) / 60
                    ),
                    0,
                ).label("total_minutes"),
            )
            .where(
                Run.user_id == user_id,
                Run.status == RunStatus.COMPLETED,
                Run.ended_at.is_not(None),
                Run.ended_at >= day_start,
                Run.ended_at < day_end,
            )
        )
        result = await self._session.execute(stmt)
        row = result.one()

        run_count = int(row.run_count or 0)
        total_minutes = int(float(row.total_minutes or 0))
        goal_total = 60
        is_completed = total_minutes >= goal_total

        streak_days = await self._calculate_streak(user_id)

        return DailyGoalResponse(
            goal_current=total_minutes,
            goal_total=goal_total,
            goal_unit="minutes",
            is_completed=is_completed,
            streak_days=streak_days,
        )

    async def _calculate_streak(self, user_id: UUID) -> int:
        tz = timezone(timedelta(hours=8))
        now_local = datetime.now(tz)
        streak = 0
        check_date = now_local.date()

        for _ in range(365):
            day_start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=tz)
            day_end = day_start + timedelta(days=1)

            stmt = select(func.count(Run.id)).where(
                Run.user_id == user_id,
                Run.status == RunStatus.COMPLETED,
                Run.ended_at.is_not(None),
                Run.ended_at >= day_start,
                Run.ended_at < day_end,
            )
            result = await self._session.execute(stmt)
            count = result.scalar() or 0

            if count > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return streak
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/repositories/test_user_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/user_repository.py tests/repositories/test_user_repository.py
git commit -m "feat: add UserRepository.get_daily_goal()"
```

---

### Task 3: 创建 UserService 和 API Route

**Files:**
- Create: `backend/app/services/user/service.py`
- Create: `backend/app/services/user/__init__.py`
- Create: `backend/app/api/v1/user.py`
- Modify: `backend/app/api/router.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/services/test_user_service.py
import pytest
from uuid import uuid4
from app.services.user.service import UserService, UserServiceError


@pytest.fixture
def service(repository):
    return UserService(repository=repository)


@pytest.mark.asyncio
async def test_get_daily_goal_success(service):
    user_id = uuid4()
    result = await service.get_daily_goal(user_id)
    assert result.goal_current >= 0
    assert result.goal_total == 60


@pytest.mark.asyncio
async def test_get_daily_goal_invalid_user(service):
    user_id = uuid4()
    result = await service.get_daily_goal(user_id)
    assert result.goal_current == 0
```

```python
# tests/api/test_user_api.py
import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_daily_goal_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/user/daily-goal")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_user_service.py tests/api/test_user_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write service**

```python
# backend/app/services/user/__init__.py
from app.services.user.service import UserService, UserServiceError

__all__ = ["UserService", "UserServiceError"]
```

```python
# backend/app/services/user/service.py
from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.schemas.user import DailyGoalResponse


class UserServiceError(Exception):
    pass


class UserService:
    def __init__(self, *, repository: UserRepository) -> None:
        self._repository = repository

    async def get_daily_goal(self, user_id: UUID) -> DailyGoalResponse:
        return await self._repository.get_daily_goal(user_id)
```

- [ ] **Step 4: Write API route**

```python
# backend/app/api/v1/user.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.user import DailyGoalResponse
from app.services.user.service import UserService

router = APIRouter(prefix="/user", tags=["user"])


async def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


async def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repository=repository)


@router.get("/daily-goal", response_model=DailyGoalResponse)
async def get_daily_goal(
    user_id: UUID = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> DailyGoalResponse:
    return await service.get_daily_goal(user_id)
```

- [ ] **Step 5: Register route in router**

```python
# backend/app/api/router.py
# Add to imports
from app.api.v1 import user

# Add to routers tuple
routers = (
    # ... existing routers
    user.router,
)
```

- [ ] **Step 6: Run tests**

Run: `cd backend && uv run pytest tests/services/test_user_service.py tests/api/test_user_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/user/ backend/app/api/v1/user.py backend/app/api/router.py
git commit -m "feat: add GET /api/v1/user/daily-goal endpoint"
```

---

### Phase 2: 前端 Bug 修复

---

### Task 4: 修复 Speed-Survival 答题流程 Bug

**Files:**
- Modify: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue:231-248`
- Modify: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.spec.ts`

- [ ] **Step 1: 添加失败测试**

```typescript
// frontend/src/pages/DungeonScholarSpeedSurvivalPage.spec.ts
it('should advance to next question when user clicks correct answer after wrong answer', async () => {
  const wrapper = mount(SpeedSurvivalPage, {
    global: { plugins: [createI18n({ ... })] },
  });
  
  // Simulate wrong answer with feedback
  await wrapper.vm.handleWrongAnswer();
  expect(wrapper.vm.showFeedback).toBe(true);
  
  // User clicks correct answer
  await wrapper.vm.chooseAnswer('true');
  
  expect(wrapper.vm.questionIndex).toBe(1);
  expect(wrapper.vm.showFeedback).toBe(false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --testPathPattern=SpeedSurvivalPage.spec.ts -v`
Expected: FAIL

- [ ] **Step 3: Fix the bug - 修改 chooseAnswer 函数**

当前代码问题 (第 231-248 行):
```typescript
// 当前逻辑 - 答错后如果有 settlement 就直接显示结算
if (!result.is_correct) {
  showFeedback.value = true;
  isSubmittingAnswer.value = false;
  if (result.settlement) {
    // ... 显示结算
    return;  // BUG: 直接返回，不允许用户继续答题
  }
  return;
}
```

修复后:
```typescript
// 修复后 - 答错后始终等待用户点击正确答案继续
if (!result.is_correct) {
  combo.value = 0;
  runStatus.value = "normal";
  showFeedback.value = true;
  isSubmittingAnswer.value = false;
  // 不再检查 settlement，答错后始终显示解析，等待用户点击正确答案
  // 如果用户点击正确答案，showFeedback 会在 watch 中被清除
  return;
}
```

同时需要添加用户点击正确答案的处理器 - 在 `showFeedback=true` 状态下，用户点击任意选项都应该清除 feedback 并继续：

```typescript
// 在 watch(currentQuestion) 中已经会清除 showFeedback
// 所以用户点击答案时会自动进入下一题
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --testPathPattern=SpeedSurvivalPage.spec.ts -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue frontend/src/pages/DungeonScholarSpeedSurvivalPage.spec.ts
git commit -m "fix: allow user to continue to next question after wrong answer in Speed Survival"
```

---

### Task 5: 修复 Knowledge Draft 答题流程 Bug

**Files:**
- Modify: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue:528-537`
- Modify: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.spec.ts`

- [ ] **Step 1: 添加失败测试**

```typescript
// frontend/src/pages/DungeonScholarKnowledgeDraftPage.spec.ts
it('should advance to next question when user clicks correct option after wrong answer', async () => {
  const wrapper = mount(KnowledgeDraftPage, {
    global: { plugins: [createI18n({ ... })] },
  });
  
  // Fill blanks and submit wrong answer
  await wrapper.vm.submitFilledAnswer();
  expect(wrapper.vm.awaitingCorrection).toBe(true);
  expect(wrapper.vm.showFeedback).toBe(true);
  
  // User clicks a correct option (in awaitingCorrection mode, any click should advance)
  await wrapper.vm.chooseOption(correctOption);
  
  expect(wrapper.vm.questionIndex).toBe(1);
  expect(wrapper.vm.awaitingCorrection).toBe(false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --testPathPattern=KnowledgeDraftPage.spec.ts -v`
Expected: FAIL

- [ ] **Step 3: Fix the bug**

当前问题代码 (第 484-499 行):
```typescript
if (awaitingCorrection.value) {
  if (!areSameOptionSet(selectedOptionIds, expectedCorrectOptionIds.value)) {
    showNotice.value = true;
    showFeedback.value = true;
    isSubmittingAnswer.value = false;
    return;  // BUG: 这里返回了，但用户还没进入下一题
  }
  awaitingCorrection.value = false;
  expectedCorrectOptionIds.value = [];
  showNotice.value = false;
  showFeedback.value = false;
  questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
  // ... 但这段代码在上面 return 之后永远不会执行
}
```

修复后 - 在 `awaitingCorrection` 状态下，用户点击选项时应该直接进入下一题，不再验证选项是否正确：

```typescript
if (awaitingCorrection.value) {
  // 用户在 awaitingCorrection 状态下点击任意选项，直接进入下一题
  awaitingCorrection.value = false;
  expectedCorrectOptionIds.value = [];
  showNotice.value = false;
  showFeedback.value = false;
  blankSelections.value = Array.from({ length: blankCount.value }, () => null);
  questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
  syncProgress();
  questionStartAt.value = Date.now();
  isSubmittingAnswer.value = false;
  return;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --testPathPattern=KnowledgeDraftPage.spec.ts -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue frontend/src/pages/DungeonScholarKnowledgeDraftPage.spec.ts
git commit -m "fix: allow user to continue to next question after wrong answer in Knowledge Draft"
```

---

### Phase 3: 前端数据接入与 I18n

---

### Task 6: 添加 getDailyGoal API 函数

**Files:**
- Create: `frontend/src/api/user.ts`

- [ ] **Step 1: 编写测试**

```typescript
// frontend/src/api/user.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { getDailyGoal } from './user';
import { apiRequest } from './http';

vi.mock('./http', () => ({
  apiRequest: vi.fn(),
}));

describe('getDailyGoal', () => {
  it('should return daily goal data', async () => {
    const mockResponse = {
      goal_current: 25,
      goal_total: 60,
      goal_unit: 'minutes',
      is_completed: false,
      streak_days: 7,
    };
    (apiRequest as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);
    
    const result = await getDailyGoal();
    expect(result.goal_current).toBe(25);
    expect(result.goal_total).toBe(60);
    expect(result.streak_days).toBe(7);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --testPathPattern=user.spec.ts -v`
Expected: FAIL

- [ ] **Step 3: Write API function**

```typescript
// frontend/src/api/user.ts
import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type DailyGoalResponse = {
  goal_current: number;
  goal_total: number;
  goal_unit: string;
  is_completed: boolean;
  streak_days: number;
};

export const getDailyGoal = async (): Promise<DailyGoalResponse> => {
  return apiRequest<DailyGoalResponse>("/api/v1/user/daily-goal", {
    method: "GET",
    headers: getAuthHeaders(),
  });
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --testPathPattern=user.spec.ts -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/user.ts frontend/src/api/user.spec.ts
git commit -m "feat: add getDailyGoal API function"
```

---

### Task 7: 修复 GameSettlementModal 支持真实数据

**Files:**
- Modify: `frontend/src/components/GameSettlementModal.vue`
- Modify: `frontend/src/components/GameSettlementModal.spec.ts`

- [ ] **Step 1: 添加测试**

```typescript
// frontend/src/components/GameSettlementModal.spec.ts
it('should display goal data from props', async () => {
  const wrapper = mount(GameSettlementModal, {
    props: {
      visible: true,
      goalCurrent: 30,
      goalTotal: 60,
      // ...
    },
  });
  
  const goalTitle = wrapper.find('.settlement-goal-title');
  expect(goalTitle.text()).toContain('30/60');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --testPathPattern=GameSettlementModal.spec.ts -v`
Expected: FAIL (if test is new)

- [ ] **Step 3: Review and update component if needed**

GameSettlementModal 已经通过 props 接收 `goalCurrent` 和 `goalTotal`，无需修改组件本身。父组件需要在打开弹窗时调用 `getDailyGoal()` API 获取真实数据。

- [ ] **Step 4: Commit (if modified)**

```bash
git add frontend/src/components/GameSettlementModal.vue
git commit -m "refactor: GameSettlementModal already supports real goal data via props"
```

---

### Task 8: 修复 ShopHeader I18n

**Files:**
- Modify: `frontend/src/components/shop/ShopHeader.vue`
- Modify: `frontend/src/i18n/index.ts`

- [ ] **Step 1: 添加测试**

```typescript
// frontend/src/components/shop/ShopHeader.spec.ts
it('should display Xi Rang for English locale', async () => {
  const wrapper = mount(ShopHeader, {
    global: { plugins: [createI18n({ locale: 'en', ... })] },
  });
  expect(wrapper.find('.shop-brand__copy').text()).toBe('Xi Rang');
});

it('should display 息壤 for Chinese locale', async () => {
  const wrapper = mount(ShopHeader, {
    global: { plugins: [createI18n({ locale: 'zh-CN', ... })] },
  });
  expect(wrapper.find('.shop-brand__copy').text()).toBe('息壤');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --testPathPattern=ShopHeader.spec.ts -v`
Expected: FAIL

- [ ] **Step 3: Update i18n with new keys**

在 `frontend/src/i18n/index.ts` 的 `shop` 部分添加:

```typescript
// English
shop: {
  brand: "Xi Rang",  // Change from hardcoded "息壤"
  bagAria: "Bag",     // New key for aria-label
  // ... existing keys
}

// Chinese Simplified
shop: {
  brand: "息壤",
  bagAria: "背包",
  // ... existing keys
}

// Chinese Traditional
shop: {
  brand: "息壤",
  bagAria: "背包",
  // ... existing keys
}
```

- [ ] **Step 4: Update ShopHeader.vue**

```vue
<!-- Before -->
<strong>息壤</strong>
<button aria-label="背包">

<!-- After -->
<strong>{{ $t("shop.brand") }}</strong>
<button :aria-label="$t('shop.bagAria')">
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npm run test -- --testPathPattern=ShopHeader.spec.ts -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/shop/ShopHeader.vue frontend/src/i18n/index.ts
git commit -m "fix: i18n for shop brand name and bag button aria-label"
```

---

### Phase 4: 集成测试与验证

---

### Task 9: 后端集成测试

- [ ] **Step 1: Run all backend tests**

Run: `cd backend && uv run pytest tests/ -q --tb=short`
Expected: ALL PASS

- [ ] **Step 2: Run linter**

Run: `cd backend && uv run ruff check app tests`
Expected: No errors

- [ ] **Step 3: Run type check**

Run: `cd backend && uv run mypy app`
Expected: No errors

---

### Task 10: 前端集成测试

- [ ] **Step 1: Run all frontend tests**

Run: `cd frontend && npm run test -- --run`
Expected: ALL PASS

- [ ] **Step 2: Run linter**

Run: `cd frontend && npm run lint`
Expected: No warnings/errors

- [ ] **Step 3: Run type check**

Run: `cd frontend && npm run typecheck`
Expected: No errors

- [ ] **Step 4: Run build**

Run: `cd frontend && npm run build`
Expected: BUILD SUCCESSFUL

---

## Dependencies

- Task 1 → Task 2 → Task 3 (sequential: schema → repository → service/route)
- Task 4 → Task 5 (parallel: both are independent bug fixes)
- Task 6 → Task 7 (sequential: API function needed before modal update)
- Task 8 (independent I18n fix)
- Task 9 (after all backend tasks complete)
- Task 10 (after all frontend tasks complete)

---

## Execution Order

1. Phase 1: Tasks 1-3 (Backend API)
2. Phase 2: Tasks 4-5 (Frontend Bug Fixes)
3. Phase 3: Tasks 6-8 (Frontend Data & I18n)
4. Phase 4: Tasks 9-10 (Integration Tests)

---

## Notes

- All commits should follow conventional commit format: `feat:`, `fix:`, `refactor:`, `test:`
- If any test fails during execution, stop and fix before proceeding
- For frontend tasks, run `npm run typecheck` after each file modification
- For backend tasks, run `uv run ruff check` after each file modification
