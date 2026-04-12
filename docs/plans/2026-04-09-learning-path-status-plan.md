# 学习路径状态管理实现计划

> **For agentic workers:** Use /execute command to implement tasks. Steps use checkbox syntax.

**Goal:** 实现学习路径的线性进度管理，类似多邻国的 locked/unlocked/completed 三状态机制

**Architecture:** 
- 后端新增 learning_paths 和 learning_path_stages 表，复用 runs 表关联 path_id
- 前端通过 API 获取路径进度，本地缓存作为降级方案
- Worker 在文档 ingestion 流程中调用 LM 生成学习路径

**Tech Stack:** 
- Backend: FastAPI, SQLAlchemy 2.0 (async), PostgreSQL
- Frontend: Vue 3 + TypeScript + Vite
- Worker: Background job system

**Design Spec:** docs/specs/2026-04-09-learning-path-status-design.md

---

## Task List

### Task 1: 创建数据库模型

**Files:**
- Create: `backend/app/db/models/learning_path.py`
- Modify: `backend/app/db/models/__init__.py`

- [ ] **Step 1: Write failing test**

```python
# tests/db/models/test_learning_path.py
import pytest
from uuid import uuid4
from app.db.models.learning_path import LearningPath, LearningPathStage

def test_learning_path_creation():
    path = LearningPath(
        id=uuid4(),
        user_id=uuid4(),
        document_id=uuid4(),
        mode="speed",
        path_structure={"stages": []}
    )
    assert path.mode == "speed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/db/models/test_learning_path.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write implementation**

```python
# backend/app/db/models/learning_path.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import ForeignKey, Integer, String, DateTime, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDPrimaryKeyMixin


class LearningPath(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_paths"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    path_structure: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=datetime.utcnow)


class LearningPathStage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_stages"
    __table_args__ = (UniqueConstraint("path_id", "stage_index"),)

    path_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"))
    stage_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    best_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/db/models/test_learning_path.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/models/learning_path.py backend/app/db/models/__init__.py
git commit -m "feat(backend): add LearningPath and LearningPathStage models"
```

---

### Task 2: 创建数据库迁移

**Files:**
- Create: `backend/alembic/versions/xxxx_add_learning_paths.py`

- [ ] **Step 1: Run autogenerate**

Run: `cd backend && uv run alembic revision --autogenerate -m "add learning_paths and learning_path_stages tables"`
Expected: Migration file created

- [ ] **Step 2: Review and commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(backend): add migration for learning_paths tables"
```

---

### Task 3: 创建后端 Repository

**Files:**
- Create: `backend/app/repositories/learning_path_repository.py`
- Modify: `backend/app/repositories/__init__.py`

- [ ] **Step 1: Write failing test**

```python
# tests/repositories/test_learning_path_repository.py
import pytest
from uuid import uuid4
from app.repositories.learning_path_repository import LearningPathRepository

@pytest.mark.asyncio
async def test_get_or_create_learning_path(db_session):
    repo = LearningPathRepository(db_session)
    document_id = uuid4()
    user_id = uuid4()
    
    path = await repo.get_or_create(document_id, user_id, "speed", ["知识点1"])
    assert path.mode == "speed"
```

- [ ] **Step 2: Write implementation**

```python
# backend/app/repositories/learning_path_repository.py
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.learning_path import LearningPath, LearningPathStage

class LearningPathRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_document(self, document_id: UUID, user_id: UUID, mode: str) -> LearningPath | None:
        result = await self.session.execute(
            select(LearningPath).where(
                LearningPath.document_id == document_id,
                LearningPath.user_id == user_id,
                LearningPath.mode == mode
            )
        )
        return result.scalar_one_or_none()

    async def create(self, document_id: UUID, user_id: UUID, mode: str, stages_data: list[dict]) -> LearningPath:
        path = LearningPath(
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            path_structure={"stages": stages_data}
        )
        self.session.add(path)
        await self.session.flush()

        for idx, stage_data in enumerate(stages_data):
            stage = LearningPathStage(
                path_id=path.id,
                stage_index=idx,
                stage_id=stage_data["stage_id"],
            )
            self.session.add(stage)

        await self.session.commit()
        await self.session.refresh(path)
        return path

    async def get_stages(self, path_id: UUID) -> list[LearningPathStage]:
        result = await self.session.execute(
            select(LearningPathStage)
            .where(LearningPathStage.path_id == path_id)
            .order_by(LearningPathStage.stage_index)
        )
        return list(result.scalars().all())

    async def update_stage_completion(self, stage_id: UUID, run_id: UUID, score: int) -> None:
        result = await self.session.execute(
            select(LearningPathStage).where(LearningPathStage.id == stage_id)
        )
        stage = result.scalar_one()
        if score > stage.best_score:
            stage.best_run_id = run_id
            stage.best_score = score
        if score > 0:
            stage.completed_at = datetime.utcnow()
        await self.session.commit()
```

- [ ] **Step 3: Run test**

Run: `cd backend && uv run pytest tests/repositories/test_learning_path_repository.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/repositories/learning_path_repository.py
git commit -m "feat(backend): add LearningPathRepository"
```

---

### Task 4: 创建后端 Schema

**Files:**
- Create: `backend/app/schemas/learning_path.py`

- [ ] **Step 1: Write schemas**

```python
# backend/app/schemas/learning_path.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from enum import StrEnum

class StageStatus(StrEnum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"

class LearningPathStageResponse(BaseModel):
    stage_index: int
    stage_id: str
    status: StageStatus
    best_run_id: UUID | None = None
    best_score: int = 0
    completed_at: datetime | None = None

class LearningPathResponse(BaseModel):
    document_id: UUID
    mode: str
    stages: list[LearningPathStageResponse]
    current_stage_index: int
    completed_stages_count: int
    total_stages_count: int

class GenerateLearningPathRequest(BaseModel):
    document_id: UUID
    mode: str
    knowledge_points: list[str]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/learning_path.py
git commit -m "feat(backend): add learning_path schemas"
```

---

### Task 5: 创建后端 Service

**Files:**
- Create: `backend/app/services/learning_path/service.py`
- Create: `backend/app/services/learning_path/__init__.py`

- [ ] **Step 1: Write service implementation**

```python
# backend/app/services/learning_path/service.py
from uuid import UUID
from app.repositories.learning_path_repository import LearningPathRepository
from app.schemas.learning_path import LearningPathStageResponse, LearningPathResponse, StageStatus

class LearningPathService:
    def __init__(self, repo: LearningPathRepository):
        self.repo = repo

    async def get_learning_path(self, document_id: UUID, user_id: UUID, mode: str) -> LearningPathResponse | None:
        path = await self.repo.get_by_document(document_id, user_id, mode)
        if not path:
            return None

        stages = await self.repo.get_stages(path.id)
        completed_count = sum(1 for s in stages if s.completed_at is not None)
        current_index = completed_count

        stage_responses = []
        for idx, stage in enumerate(stages):
            if stage.completed_at:
                status = StageStatus.COMPLETED
            elif idx == current_index:
                status = StageStatus.UNLOCKED
            else:
                status = StageStatus.LOCKED

            stage_responses.append(LearningPathStageResponse(
                stage_index=idx,
                stage_id=stage.stage_id,
                status=status,
                best_run_id=stage.best_run_id,
                best_score=stage.best_score,
                completed_at=stage.completed_at
            ))

        return LearningPathResponse(
            document_id=document_id,
            mode=mode,
            stages=stage_responses,
            current_stage_index=current_index,
            completed_stages_count=completed_count,
            total_stages_count=len(stages)
        )

    async def mark_stage_completed(self, path_id: UUID, stage_index: int, run_id: UUID, score: int) -> None:
        stages = await self.repo.get_stages(path_id)
        if stage_index < len(stages):
            await self.repo.update_stage_completion(stages[stage_index].id, run_id, score)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/learning_path/
git commit -m "feat(backend): add LearningPathService"
```

---

### Task 6: 创建后端 API 端点

**Files:**
- Create: `backend/app/api/v1/learning_paths.py`

- [ ] **Step 1: Write API endpoints**

```python
# backend/app/api/v1/learning_paths.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.learning_path.service import LearningPathService
from app.repositories.learning_path_repository import LearningPathRepository
from app.schemas.learning_path import LearningPathResponse, GenerateLearningPathRequest
from app.db.session import async_session
from app.core.security import get_current_user

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])

async def get_service() -> LearningPathService:
    async with async_session() as session:
        repo = LearningPathRepository(session)
        yield LearningPathService(repo)

@router.get("", response_model=LearningPathResponse)
async def get_learning_path(
    document_id: UUID,
    mode: str,
    service: LearningPathService = Depends(get_service),
    user=Depends(get_current_user),
):
    result = await service.get_learning_path(document_id, user.id, mode)
    if not result:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return result

@router.post("/generate")
async def generate_learning_path(
    request: GenerateLearningPathRequest,
    service: LearningPathService = Depends(get_service),
    user=Depends(get_current_user),
):
    # TODO: Call LLM to generate path structure
    return {"message": "Not implemented yet"}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/v1/learning_paths.py
git commit -m "feat(backend): add learning_paths API endpoints"
```

---

### Task 7: 创建前端 API Client

**Files:**
- Create: `frontend/src/api/learningPaths.ts`

- [ ] **Step 1: Write API client**

```typescript
// frontend/src/api/learningPaths.ts
import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type StageStatus = "locked" | "unlocked" | "completed";

export type LearningPathStage = {
  stage_index: number;
  stage_id: string;
  status: StageStatus;
  best_run_id: string | null;
  best_score: number;
  completed_at: string | null;
};

export type LearningPathResponse = {
  document_id: string;
  mode: string;
  stages: LearningPathStage[];
  current_stage_index: number;
  completed_stages_count: number;
  total_stages_count: number;
};

export const getLearningPath = async (
  documentId: string,
  mode: "speed" | "draft" | "endless"
): Promise<LearningPathResponse> => {
  return apiRequest<LearningPathResponse>(
    `/api/v1/learning-paths?document_id=${encodeURIComponent(documentId)}&mode=${mode}`,
    { headers: getAuthHeaders() }
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/learningPaths.ts
git commit -m "feat(frontend): add learning paths API client"
```

---

### Task 8: 创建前端 Composable

**Files:**
- Create: `frontend/src/composables/useLearningPath.ts`

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/composables/useLearningPath.spec.ts
import { describe, it, expect, vi } from "vitest";
import { ref } from "vue";
import { useLearningPath } from "./useLearningPath";

vi.mock("../api/learningPaths", () => ({
  getLearningPath: vi.fn()
}));

describe("useLearningPath", () => {
  it("should return locked status for future stages", () => {
    const { getStageStatus } = useLearningPath("doc-1", "speed");
    expect(getStageStatus(0)).toBe("unlocked");
    expect(getStageStatus(1)).toBe("locked");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/composables/useLearningPath.spec.ts`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```typescript
// frontend/src/composables/useLearningPath.ts
import { ref, computed } from "vue";
import { getLearningPath, type LearningPathStage, type StageStatus } from "../api/learningPaths";

const CACHE_KEY_PREFIX = "xirang:learning-path:";

export function useLearningPath(documentId: string, mode: "speed" | "draft" | "endless") {
  const stages = ref<LearningPathStage[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const currentStageIndex = computed(() => {
    const completedIndex = stages.value.findIndex(s => s.status !== "completed");
    return completedIndex === -1 ? stages.value.length : completedIndex;
  });

  const cacheKey = `${CACHE_KEY_PREFIX}${documentId}:${mode}`;

  const loadFromCache = () => {
    if (typeof window === "undefined") return null;
    const cached = localStorage.getItem(cacheKey);
    return cached ? JSON.parse(cached) : null;
  };

  const saveToCache = (data: LearningPathStage[]) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(cacheKey, JSON.stringify(data));
  };

  const fetchProgress = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await getLearningPath(documentId, mode);
      stages.value = response.stages;
      saveToCache(response.stages);
    } catch (e) {
      const cached = loadFromCache();
      if (cached) {
        stages.value = cached;
      } else {
        error.value = "Failed to load learning path";
      }
    } finally {
      isLoading.value = false;
    }
  };

  const getStageStatus = (index: number): StageStatus => {
    if (index < currentStageIndex.value) return "completed";
    if (index === currentStageIndex.value) return "unlocked";
    return "locked";
  };

  return {
    stages,
    isLoading,
    error,
    currentStageIndex,
    fetchProgress,
    getStageStatus,
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/composables/useLearningPath.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useLearningPath.ts frontend/src/composables/useLearningPath.spec.ts
git commit -m "feat(frontend): add useLearningPath composable"
```

---

### Task 9: 修改前端 LevelPathPage

**Files:**
- Modify: `frontend/src/pages/DungeonScholarLevelPathPage.vue:1-528`

- [ ] **Step 1: Add status to PathNode type and node classes**

Modify `PathNode` type to add `status` field:
```typescript
type PathNode = {
  id: string;
  label: string;
  type: "battle" | "study" | "checkpoint" | "boss" | "speed" | "draft" | "review";
  description: string;
  floor?: number;
  status: "locked" | "unlocked" | "completed";
};
```

- [ ] **Step 2: Update mapOptionToNode to use status from API or compute locally**

```typescript
const mapOptionToNode = (option: RunPathOption, stageStatus?: StageStatus): PathNode => {
  // ... existing code ...
  return {
    id: option.path_id,
    label: option.label,
    // ... existing fields ...
    status: stageStatus || "locked",
  };
};
```

- [ ] **Step 3: Add CSS for locked/unlocked/completed states**

```css
.path-node--locked {
  opacity: 0.5;
  cursor: not-allowed;
}

.path-node--unlocked {
  border-color: var(--color-primary-500);
  animation: pulse 2s infinite;
}

.path-node--completed {
  border-color: var(--color-success);
  animation: glow 1.5s ease-in-out infinite alternate;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--color-primary-rgb), 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(var(--color-primary-rgb), 0); }
}

@keyframes glow {
  from { box-shadow: 0 0 4px var(--color-success); }
  to { box-shadow: 0 0 12px var(--color-success); }
}
```

- [ ] **Step 4: Update node click handler to check status**

```typescript
const handleNodeClick = (node: PathNode) => {
  if (node.status === "locked") {
    // Show toast message
    return;
  }
  selectedNodeId.value = node.id;
};
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DungeonScholarLevelPathPage.vue
git commit -m "feat(frontend): add locked/unlocked/completed states to LevelPathPage"
```

---

### Task 10: 集成测试

**Files:**
- Create: `tests/api/test_learning_paths_api.py`
- Create: `frontend/src/pages/DungeonScholarLevelPathPage.spec.ts`

- [ ] **Step 1: Run backend integration test**

Run: `cd backend && uv run pytest tests/api/test_learning_paths_api.py -v`

- [ ] **Step 2: Run frontend e2e test**

Run: `cd frontend && npm run test -- src/pages/DungeonScholarLevelPathPage.spec.ts`

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "test: add learning paths integration tests"
```

---

## Dependencies

1. Task 1 → Task 2 (migration depends on models)
2. Task 1 → Task 3 (repository uses models)
3. Task 3 → Task 4 (service uses repo)
4. Task 4 → Task 5 (API uses schemas)
5. Task 5 → Task 6 (API endpoints use service)
6. Task 6 → Task 7 (frontend API client calls backend)
7. Task 7 → Task 8 (composable uses API client)
8. Task 8 → Task 9 (page uses composable)
9. Task 9 → Task 10 (tests verify integration)

---

## Execution Order

Use `/execute <task-number>` to run individual tasks, or `/execute all` to run sequentially.
