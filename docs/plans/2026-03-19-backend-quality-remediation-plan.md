# Backend Quality Remediation Plan

> For agentic workers: use `/execute` to run tasks in order.

**Goal:** 在不改变业务行为与API契约测试结果的前提下，修复 2026-03-19 评估报告中的质量问题，提升可读性与类型一致性，并将综合质量评分提升到 90+。

**Scope:** `backend/app`, `backend/tests`, `AGENTS.md`, `docs/reviews`

---

## Acceptance Criteria

1. `uv run pytest tests -q --tb=short` 全量通过。
2. `uv run ruff check app tests` 无错误。
3. `uv run mypy app` 无错误。
4. `docs/reviews` 生成最新质量报告，分数 >= 90。
5. `AGENTS.md` 保持并明确 backend 使用 `uv` 的规范。

---

## Task 1: 修复剩余 Ruff 问题（B904/F841/TC/SIM）

**Files**
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/v1/documents.py`
- Modify: `backend/app/services/auth/service.py`
- Modify: `backend/app/services/documents/service.py`
- Modify: `backend/app/services/questions/validator.py`
- Modify: `backend/app/services/review/facade.py`

**QA**
- Run: `cd backend && uv run ruff check app tests`
- Expect: no errors.

## Task 2: API 层类型补齐（no-untyped-def/type-arg）

**Files**
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/v1/documents.py`
- Modify: `backend/app/api/v1/document_ai.py`
- Modify: `backend/app/api/v1/feedback.py`
- Modify: `backend/app/api/v1/runs.py`
- Modify: `backend/app/api/v1/jobs.py`
- Modify: `backend/app/api/v1/leaderboard.py`
- Modify: `backend/app/api/v1/profile.py`
- Modify: `backend/app/api/v1/settings.py`
- Modify: `backend/app/api/v1/shop.py`

**QA**
- Run: `cd backend && uv run mypy app`
- Expect: API 文件相关 no-untyped-def/type-arg 清零。

## Task 3: Service/Protocol 类型一致性收敛

**Files**
- Modify: `backend/app/services/auth/service.py`
- Modify: `backend/app/services/documents/service.py`
- Modify: `backend/app/services/documents/ask_service.py`
- Modify: `backend/app/services/documents/recommendation_service.py`
- Modify: `backend/app/services/questions/generator.py`
- Modify: `backend/app/services/review/facade.py`
- Modify: `backend/app/services/llm/provider_registry.py`
- Modify: `backend/app/integrations/agents/client.py`
- Modify: `backend/app/integrations/pageindex/client.py`
- Modify: `backend/app/workers/feedback_learning_job.py`
- Modify: `backend/app/workers/main.py`
- Modify: `backend/app/schemas/review.py`
- Modify: `backend/app/repositories/document_repository.py`

**QA**
- Run: `cd backend && uv run mypy app`
- Expect: zero errors.

## Task 4: 回归验证与质量复评

**Files**
- Modify: `docs/reviews/2026-03-19-backend-quality.md` (if superseded)
- Create: `docs/reviews/2026-03-19-backend-quality-v2.md`

**QA**
- Run: `cd backend && uv run pytest tests -q --tb=short`
- Run: `cd backend && uv run ruff check app tests`
- Run: `cd backend && uv run mypy app`
- Expect: tests/lint/typecheck all green; report score >= 90.
