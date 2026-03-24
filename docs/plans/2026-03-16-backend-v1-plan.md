# Xirang Backend V1 Work Plan

## TL;DR

> **Quick Summary**: Build the phase-1 backend closed loop for Xirang with FastAPI, SQLAlchemy, PostgreSQL, pgvector, self-hosted PageIndex, and OpenAI Agents SDK, while explicitly reserving OAuth, payment, weekly seasons, and advanced model routing for phase 2.
>
> **Deliverables**:
> - `backend/` Python service with `auth`, `documents`, `jobs`, `runs`, `review`, `profile`, `settings`, `wallet`, `shop`, and minimal `leaderboard`
> - Root-level `scripts/init_db.py` for local DB bootstrap
> - Separate worker process driven by a job table
> - Feedback persistence + self-learning agent + reviewable rule repository
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Foundation -> DB/Models -> Upload/Worker/PageIndex -> Question Pipeline -> Runs/Settlement -> Feedback/Review -> Integration

---

## Context

### Original Request
Create and refine an implementation plan for the backend after front-end alignment, database design, and technical stack selection. The final plan must prioritize the phase-1 core loop, support later deployment to Vercel (frontend) and Render (backend), and prepare the system for Supabase-backed production data and phase-2 expansion.

### Interview Summary

**Phase / Scope Decisions**
- Phase 1 builds the core learning loop first.
- Phase 2 adds OAuth, full payment, weekly seasons, quest operations backend, and advanced model switching.
- Account deletion is phase 2 only.

**Environment / Deployment Decisions**
- Local single-machine development is the default development and acceptance environment.
- Local development DB uses a locally installed PostgreSQL instance.
- Production DB targets Supabase.
- Frontend deployment target is Vercel.
- Backend deployment target is Render.
- Storage is dual-mode: local filesystem in dev, object storage when deployed.

**Document / Ingestion Decisions**
- Documents appear immediately in the library after upload with `processing` status.
- Failed documents are retained and may be retried.
- Phase-1 input formats: PDF, DOCX, TXT, Markdown.
- Document becomes `ready` only after the full base question bank is generated.

**Question / Game Decisions**
- Phase-1 question types: single choice, multiple choice, true/false.
- Fill-in-the-blank moves to phase 2.
- The three modes share one base question bank but use different selection and ordering strategies.
- Settlement rewards are fully formula/rule based, not AI-determined.

**AI / Retrieval Decisions**
- Ask scope in phase 1 is current document only.
- Later it may evolve to current document + historical mistakes.
- Study recommendation returns sections/knowledge points + reasons + next-step suggestions.
- PageIndex remains the primary document retrieval backend.
- pgvector remains limited to mistakes / review enhancement.

**Feedback / Self-Learning Decisions**
- "This question is wrong" feedback must persist in a dedicated feedback domain.
- A self-learning agent built with OpenAI Agents SDK must summarize feedback and write improvement suggestions to a reviewable rule repository.
- In phase 1, rules are generated and stored for review; they do not auto-modify live question generation or prompts.

**Economy / Community Decisions**
- Wallet requires a real ledger, not a balance-only shortcut.
- Shop in phase 1 must support in-app coin deduction, item purchase, and inventory increment.
- Full payment flow is phase 2.
- Leaderboard in phase 1 is global cumulative only.
- Weekly season and promotion logic remain phase 2.

**Testing / Execution Decisions**
- Testing must cover unit + integration + full E2E key flows.
- Background jobs in phase 1 use a separate worker process plus job table.
- Phase 2 may upgrade background work to Celery/Redis or equivalent.

### Research Findings
- `frontend/` is the only implemented app and still uses mocked state for upload, wallet, settlement, and leaderboard flows.
- `docs/specs/2026-03-16-backend-v1-design.md` is complete enough for implementation planning.
- `Design Document/database.md` contains a broad DDL baseline; implementation must constrain phase-1 ORM scope to avoid accidental phase-2 creep.
- Desktop `planner` sessions are effectively read-only in practice; implementation should be executed in `build` sessions.

### Metis Review

**Identified Gaps (addressed in this plan)**
- Missing explicit phase-1 scope locks -> added in guardrails and non-goals.
- Missing file-size / retry defaults -> added as plan defaults.
- Missing worker-process clarity -> fixed to job-table + separate worker in phase 1.
- Missing self-learning feedback loop task -> added as a dedicated work item.
- Missing operational edge cases -> folded into acceptance and verification criteria.

---

## Work Objectives

### Core Objective
Deliver a production-shaped but phase-1-constrained backend that lets users register, upload supported documents, wait for processing, enter any of the three modes, receive deterministic settlement, purchase in-app items with coins, report bad questions, and receive AI-enhanced review support.

### Concrete Deliverables
- `backend/` service scaffold with FastAPI app factory and structured configuration
- Alembic migrations + SQLAlchemy models for phase-1 domains and phase-2 extension points
- Root bootstrap script: `scripts/init_db.py`
- Auth API with email/password + session-backed refresh rotation
- Document upload + processing job + retryable failure handling
- Self-hosted PageIndex adapter and document ask/recommend APIs
- Question generation pipeline using OpenAI Agents SDK
- Run lifecycle, answer submission, deterministic settlement, and wallet ledger updates
- Feedback persistence, self-learning agent summaries, and reviewable rule repository
- Phase-1 support APIs: profile, settings, wallet, shop purchase, global leaderboard
- End-to-end verification and phase-2 follow-up tracking

### Definition of Done
- [ ] A user can register, login, refresh, and logout successfully.
- [ ] A user can upload a PDF/DOCX/TXT/Markdown file and immediately see it as `processing`.
- [ ] Failed uploads remain visible and can be retried.
- [ ] A document becomes `ready` only after indexing + question generation are complete.
- [ ] Any of the three modes can start from the same base question bank.
- [ ] Settlement updates the wallet ledger and returns stable XP/coin/combo fields.
- [ ] Feedback on bad questions is persisted and summarized by the self-learning agent.
- [ ] In-app shop purchases consume coins and increment inventory.
- [ ] Global leaderboard reads work.
- [ ] Tests pass at unit, integration, and E2E levels.

### Must Have
- Separate worker process for long-running jobs in phase 1
- Storage abstraction with local filesystem + object-storage implementations
- Feedback domain + reviewable rule repository
- Deterministic reward formulas
- Current-document-only ask scope in phase 1
- Real wallet ledger writes

### Must NOT Have (Guardrails)
- No OAuth endpoints in phase 1
- No real payment gateway or subscription billing in phase 1
- No weekly seasons or promotion calculations in phase 1
- No fill-in-the-blank generation or grading in phase 1
- No cross-document free-form ask in phase 1
- No Celery/Redis queue stack in phase 1
- No auto-application of self-learning rules in phase 1

---

## Defaults Applied

- **File size limit**: default hard limit `50MB`; recommended UX guidance `20MB` and below.
- **Retry policy**: document processing and feedback-learning jobs default to `3` attempts with exponential backoff.
- **Question generation readiness**: a document is not marked `ready` until a valid base question bank exists.
- **Feedback learning mode**: asynchronous only, never synchronous on the request thread.
- **Storage path (local dev)**: default local upload root under `backend/.data/uploads/`.
- **Timezone baseline for future season logic**: `Asia/Shanghai`.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (backend is new)
- **Automated tests**: YES
- **Framework**: `pytest` + `httpx` + phase-1 E2E test harness
- **Mode**: Unit + integration + full key E2E

### QA Policy
Every major task must define:
- RED test first
- GREEN implementation second
- REFACTOR cleanup third
- command-based verification fourth

Primary verification modes:
- **API/Backend**: `pytest`, `httpx`, direct service tests, local smoke server checks
- **DB**: Alembic upgrade + bootstrap script + pgvector smoke query
- **Worker**: job-polling + state transition tests
- **E2E**: register -> upload -> process -> create run -> answer -> settlement -> feedback -> review

### Required Evidence
- Test outputs from `pytest`
- Lint/type output from `ruff` and `mypy`
- migration/bootstrap command logs
- one reproducible local smoke run note in backend README

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Start Immediately - foundation)
- Task 1: Phase-1 scope lock and backend skeleton
- Task 2: FastAPI app shell and core config
- Task 3: DB bootstrap, Alembic, and init script
- Task 4: Phase-1 ORM models
- Task 5: Storage abstraction baseline

Wave 2 (After Wave 1 - core services)
- Task 6: Auth service and auth API
- Task 7: Upload, documents, jobs, and retry flow
- Task 8: Separate worker process and job runner
- Task 9: Self-hosted PageIndex adapter and ask/recommend API
- Task 10: Question generation pipeline and provider registry

Wave 3 (After Wave 2 - gameplay and learning loop)
- Task 11: Run lifecycle, answer submission, and settlement
- Task 12: Feedback domain, pgvector review, and self-learning rule repository
- Task 13: Profile, settings, wallet, shop purchase, inventory, and global leaderboard

Wave 4 (After Wave 3 - integration and hardening)
- Task 14: Full E2E verification, docs, and phase-2 guardrails

Wave FINAL (After all tasks - review)
- F1: Plan compliance audit
- F2: Code quality review
- F3: E2E/manual scenario execution
- F4: Scope fidelity check

### Dependency Matrix
- **1**: none -> 14
- **2**: 1 -> 6,7,8,9,10,11,13,14
- **3**: 1 -> 4,6,7,8,10,11,12,13,14
- **4**: 3 -> 6,7,10,11,12,13,14
- **5**: 1 -> 7,14
- **6**: 2,4 -> 11,13,14
- **7**: 2,4,5 -> 9,10,11,12,14
- **8**: 2,3 -> 10,12,14
- **9**: 2,7 -> 10,12,14
- **10**: 4,7,8,9 -> 11,14
- **11**: 4,6,7,10 -> 12,13,14
- **12**: 7,8,9,11 -> 14
- **13**: 4,6,11 -> 14
- **14**: 1-13 -> FINAL

### Agent Dispatch Summary
- **Wave 1**: `quick` / `unspecified-high` / `writing`
- **Wave 2**: `quick`, `unspecified-high`, `deep`
- **Wave 3**: `deep`, `unspecified-high`
- **Wave 4**: `deep`
- **Final**: `oracle`, `unspecified-high`, `deep`

---

## TODOs

### Task 1: Lock Phase-1 Scope and Bootstrap the Python Project

**What to do**:
- Create a short phase-1 scope-lock document for implementation workers.
- Initialize `backend/` with `pyproject.toml`, `.env.example`, package roots, and command documentation.
- Encode non-goals clearly so phase-2 work does not leak into phase 1.

**Files**:
- Create: `backend/pyproject.toml`
- Create: `backend/README.md`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_project_layout.py`
- Create: `docs/backend-phase1-scope.md`
- Create: `scripts/README.md`

**TDD Steps**:
- RED: add `backend/tests/test_project_layout.py`
- GREEN: create backend skeleton and scope-lock doc
- REFACTOR: remove duplicated setup notes and centralize commands

**Verify**:
- `python -m pytest backend/tests/test_project_layout.py`
- `python -m ruff check backend`

**Commit**: `chore: bootstrap backend project and scope lock`

---

### Task 2: Build FastAPI App Shell and Typed Core Configuration

**What to do**:
- Implement app factory, API router registration, settings loader, and basic structured logging.
- Expose `/health`, `/api/v1/health`, and `/api/v1/version`.

**Files**:
- Create: `backend/app/main.py`
- Create: `backend/app/api/router.py`
- Create: `backend/app/api/v1/system.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/logging.py`
- Create: `backend/tests/api/test_system.py`

**TDD Steps**:
- RED: health/version API tests
- GREEN: app shell and router wiring
- REFACTOR: keep config concerns in `core/`

**Verify**:
- `python -m pytest backend/tests/api/test_system.py`
- `python -m mypy backend/app`

**Commit**: `feat: add fastapi app shell and system routes`

---

### Task 3: Add Database Bootstrap, Alembic, and Root Init Script

**What to do**:
- Add SQLAlchemy engine/session bootstrap.
- Configure Alembic.
- Add root `scripts/init_db.py` to create required extensions and run migrations.
- Support local PostgreSQL now and Supabase-compatible production config later.

**Files**:
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `scripts/init_db.py`
- Create: `backend/tests/db/test_session.py`

**TDD Steps**:
- RED: DB session/bootstrap tests
- GREEN: engine/session/bootstrap script
- REFACTOR: isolate DB bootstrap from business services

**Verify**:
- `python -m pytest backend/tests/db/test_session.py`
- `python scripts/init_db.py --help`
- `python -m alembic -c backend/alembic.ini upgrade head`

**Commit**: `feat: add db bootstrap and init script`

---

### Task 4: Implement Phase-1 ORM Models and Phase-2 Extension Points

**What to do**:
- Translate only the needed phase-1 DDL into ORM models.
- Preserve extension points for OAuth, seasons, and payment without implementing them.

**Files**:
- Create: `backend/app/db/models/auth.py`
- Create: `backend/app/db/models/profile.py`
- Create: `backend/app/db/models/documents.py`
- Create: `backend/app/db/models/questions.py`
- Create: `backend/app/db/models/runs.py`
- Create: `backend/app/db/models/review.py`
- Create: `backend/app/db/models/economy.py`
- Create: `backend/tests/db/test_models_phase1.py`
- Modify: `backend/app/db/models/__init__.py`

**TDD Steps**:
- RED: metadata/table coverage tests
- GREEN: ORM model implementation
- REFACTOR: extract common timestamp/value helpers only when duplication is proven

**Verify**:
- `python -m pytest backend/tests/db/test_models_phase1.py`
- `python -m alembic -c backend/alembic.ini revision --autogenerate -m "phase1 models"`

**Commit**: `feat: add phase1 orm models`

---

### Task 5: Add Storage Adapter for Local Filesystem and Production Object Storage

**What to do**:
- Create storage abstraction with local filesystem implementation for dev.
- Define production object-storage adapter seam for deployed environments.
- Enforce file-size and file-type validation at the boundary.

**Files**:
- Create: `backend/app/services/documents/storage.py`
- Create: `backend/app/services/documents/storage_local.py`
- Create: `backend/app/services/documents/storage_object.py`
- Create: `backend/tests/services/test_storage_adapter.py`

**TDD Steps**:
- RED: storage contract tests and file validation tests
- GREEN: local/object adapters and validation rules
- REFACTOR: remove env branching from API layer and keep it in adapter factory

**Verify**:
- `python -m pytest backend/tests/services/test_storage_adapter.py`

**Commit**: `feat: add storage abstraction for uploads`

---

### Task 6: Implement Auth Service and `/api/v1/auth/*` Endpoints

**What to do**:
- Add register/login/refresh/logout/me APIs.
- Use password hashing and session-backed refresh rotation.
- Keep account deletion out of scope for phase 1.

**Files**:
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/repositories/auth_repository.py`
- Create: `backend/app/services/auth/passwords.py`
- Create: `backend/app/services/auth/tokens.py`
- Create: `backend/app/services/auth/service.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/tests/services/test_auth_service.py`
- Create: `backend/tests/api/test_auth_api.py`

**TDD Steps**:
- RED: auth unit/API tests for register/login/refresh/logout/me and failure cases
- GREEN: auth implementation
- REFACTOR: keep token logic separate from orchestration

**Verify**:
- `python -m pytest backend/tests/services/test_auth_service.py backend/tests/api/test_auth_api.py`
- `python -m mypy backend/
app`

**Commit**: `feat: add email auth and refresh rotation`

---

### Task 7: Implement Document Upload, Immediate Visibility, Job Tracking, and Retry Flow

**What to do**:
- Let uploaded documents appear immediately with `processing` status.
- Persist documents and job records.
- Support retry for failed documents instead of requiring re-upload.

**Files**:
- Create: `backend/app/schemas/documents.py`
- Create: `backend/app/repositories/document_repository.py`
- Create: `backend/app/services/documents/jobs.py`
- Create: `backend/app/services/documents/service.py`
- Create: `backend/app/api/v1/documents.py`
- Create: `backend/app/api/v1/jobs.py`
- Create: `backend/tests/services/test_document_service.py`
- Create: `backend/tests/api/test_document_api.py`

**TDD Steps**:
- RED: upload/job/status/retry tests
- GREEN: document creation, file persistence, job persistence, retry endpoint/service
- REFACTOR: keep upload request thin and move orchestration into services

**Verify**:
- `python -m pytest backend/tests/services/test_document_service.py backend/tests/api/test_document_api.py`

**Commit**: `feat: add upload jobs and retryable document states`

---

### Task 8: Implement Separate Worker Process and Job Runner

**What to do**:
- Add an explicit worker entrypoint that polls the job table and executes long-running tasks.
- Phase 1 worker responsibilities: document processing, PageIndex indexing, question generation, embeddings, self-learning summaries.

**Files**:
- Create: `backend/app/workers/main.py`
- Create: `backend/app/workers/job_runner.py`
- Create: `backend/app/workers/registry.py`
- Create: `backend/tests/workers/test_job_runner.py`

**TDD Steps**:
- RED: job-claiming and retry-behavior tests
- GREEN: worker process and registry implementation
- REFACTOR: isolate worker-loop config and job handlers

**Verify**:
- `python -m pytest backend/tests/workers/test_job_runner.py`

**Commit**: `feat: add separate phase1 worker process`

---

### Task 9: Add Self-Hosted PageIndex Adapter and Current-Document Ask/Recommendation API

**What to do**:
- Add self-hosted PageIndex client and adapter.
- Implement current-document-only ask.
- Implement study recommendation responses with reason + next-step suggestion.

**Files**:
- Create: `backend/app/integrations/pageindex/client.py`
- Create: `backend/app/services/retrieval/pageindex_backend.py`
- Create: `backend/app/services/documents/ask_service.py`
- Create: `backend/app/services/documents/recommendation_service.py`
- Create: `backend/app/api/v1/document_ai.py`
- Create: `backend/tests/integrations/test_pageindex_adapter.py`
- Create: `backend/tests/api/test_document_ai_api.py`

**TDD Steps**:
- RED: adapter contract tests + ask/recommend API tests
- GREEN: PageIndex adapter and API services
- REFACTOR: vendor payloads remain inside the adapter only

**Verify**:
- `python -m pytest backend/tests/integrations/test_pageindex_adapter.py backend/tests/api/test_document_ai_api.py`

**Commit**: `feat: add pageindex ask and recommendation flow`

---

### Task 10: Implement Provider Registry and Question Generation Pipeline

**What to do**:
- Add a provider registry even though phase 1 uses one configured model.
- Use OpenAI Agents SDK to generate structured base questions.
- Support only single choice, multiple choice, and true/false in phase 1.

**Files**:
- Create: `backend/app/integrations/agents/client.py`
- Create: `backend/app/services/llm/provider_registry.py`
- Create: `backend/app/services/questions/generator.py`
- Create: `backend/app/services/questions/validator.py`
- Create: `backend/tests/services/test_question_generator.py`
- Create: `backend/tests/workers/test_ingestion_pipeline.py`

**TDD Steps**:
- RED: generation schema tests and ingestion state-transition tests
- GREEN: generator + validator + worker handler
- REFACTOR: keep prompt/schema logic separate from persistence logic

**Verify**:
- `python -m pytest backend/tests/services/test_question_generator.py backend/tests/workers/test_ingestion_pipeline.py`

**Commit**: `feat: add structured question generation pipeline`

---

### Task 11: Implement Run Lifecycle, Mode Strategies, and Deterministic Settlement

**What to do**:
- Add unified run creation and answer submission APIs.
- Reuse one base question bank with per-mode selection/sorting strategies.
- Compute XP/coins/combo/multipliers strictly via rule formulas.

**Files**:
- Create: `backend/app/schemas/runs.py`
- Create: `backend/app/repositories/run_repository.py`
- Create: `backend/app/services/runs/question_selector.py`
- Create: `backend/app/services/runs/scoring.py`
- Create: `backend/app/services/runs/settlement.py`
- Create: `backend/app/services/runs/service.py`
- Create: `backend/app/api/v1/runs.py`
- Create: `backend/tests/services/test_run_service.py`
- Create: `backend/tests/api/test_runs_api.py`

**TDD Steps**:
- RED: create-run / submit-answer / idempotency / settlement tests
- GREEN: run service + scoring + settlement implementation
- REFACTOR: move per-mode differences into strategy modules only

**Verify**:
- `python -m pytest backend/tests/services/test_run_service.py backend/tests/api/test_runs_api.py`

**Commit**: `feat: add run lifecycle and rule-based settlements`

---

### Task 12: Implement Feedback Domain, pgvector Review, and Self-Learning Rule Repository

**What to do**:
- Persist "this question is wrong" feedback in a dedicated feedback domain.
- Persist mistake and feedback vectors for review enhancement.
- Add self-learning worker jobs that summarize feedback and write suggestions into a reviewable rule repository.
- Do not auto-apply generated rules in phase 1.

**Files**:
- Create: `backend/app/schemas/review.py`
- Create: `backend/app/repositories/review_repository.py`
- Create: `backend/app/services/review/embeddings.py`
- Create: `backend/app/services/review/vector_backend.py`
- Create: `backend/app/services/review/explainer.py`
- Create: `backend/app/services/review/feedback_learning.py`
- Create: `backend/app/api/v1/review.py`
- Create: `backend/app/api/v1/feedback.py`
- Create: `backend/app/workers/feedback_learning_job.py`
- Create: `docs/review-rules/README.md`
- Create: `backend/tests/services/test_review_service.py`
- Create: `backend/tests/api/test_review_api.py`

**TDD Steps**:
- RED: feedback persistence tests, vector lookup tests, rule-generation output tests
- GREEN: feedback + review + self-learning implementation
- REFACTOR: separate feedback capture, embedding, explain, and rule-writing services

**Verify**:
- `python -m pytest backend/tests/services/test_review_service.py backend/tests/api/test_review_api.py`

**Commit**: `feat: add feedback learning and review intelligence`

---

### Task 13: Implement Profile, Settings, Wallet Ledger, Shop Purchase, Inventory, and Global Leaderboard

**What to do**:
- Add profile/settings CRUD.
- Add wallet balance projection from ledger.
- Add in-app shop purchase using coin deduction and inventory increment.
- Add read-only global cumulative leaderboard.

**Files**:
- Create: `backend/app/schemas/profile.py`
- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/schemas/shop.py`
- Create: `backend/app/services/profile/service.py`
- Create: `backend/app/services/settings/service.py`
- Create: `backend/app/services/wallet/service.py`
- Create: `backend/app/services/shop/service.py`
- Create: `backend/app/services/leaderboard/service.py`
- Create: `backend/app/api/v1/profile.py`
- Create: `backend/app/api/v1/settings.py`
- Create: `backend/app/api/v1/shop.py`
- Create: `backend/app/api/v1/leaderboard.py`
- Create: `backend/tests/api/test_profile_settings_api.py`
- Create: `backend/tests/api/test_shop_api.py`

**TDD Steps**:
- RED: profile/settings/shop/leaderboard tests
- GREEN: support APIs and ledger-backed purchase flow
- REFACTOR: keep payment gateways out of the phase-1 shop layer

**Verify**:
- `python -m pytest backend/tests/api/test_profile_settings_api.py backend/tests/api/test_shop_api.py`

**Commit**: `feat: add support surfaces wallet and shop flow`

---

### Task 14: Full E2E Verification, Docs, and Phase-2 Follow-Ups

**What to do**:
- Build the full E2E phase-1 path.
- Document local setup and deployment assumptions.
- Track every phase-2 reserved feature explicitly.

**Files**:
- Create: `backend/tests/integration/test_phase1_closed_loop.py`
- Create: `backend/tests/fixtures/`
- Modify: `backend/README.md`
- Create: `docs/backend-phase2-followups.md`

**TDD Steps**:
- RED: full end-to-end closed-loop test
- GREEN: final glue and docs
- REFACTOR: remove dead bootstrap code and stale env docs

**Verify**:
- `python -m pytest backend/tests`
- `python -m ruff check backend`
- `python -m mypy backend/app`
- `python scripts/init_db.py`
- local FastAPI smoke run

**Commit**: `test: verify backend phase1 closed loop`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — verify every phase-1 must-have exists and every phase-2 non-goal is still absent.
- [ ] F2. **Code Quality Review** — run lint, types, tests, and inspect for accidental over-abstraction or phase-2 leakage.
- [ ] F3. **Scenario Verification** — run the full user journey plus failure paths: bad upload, failed processing retry, invalid login, duplicate answer submit, insufficient coins.
- [ ] F4. **Scope Fidelity Check** — compare changed files and APIs against the scope-lock document.

---

## Commit Strategy

- Foundation commits: bootstrap / app shell / db bootstrap / models
- Service commits: auth / documents / worker / retrieval / question generation / runs / review / support surfaces
- Final commit: integration verification and docs

---

## Success Criteria

### Verification Commands
```bash
python -m pytest backend/tests
python -m ruff check backend
python -m mypy backend/app
python scripts/init_db.py
```

### Final Checklist
- [ ] Phase-1 scope lock exists and is respected.
- [ ] Backend can run locally against local PostgreSQL.
- [ ] Production config shape is compatible with Render + Supabase + object storage.
- [ ] Upload -> processing -> ready -> run -> settlement -> feedback -> review works.
- [ ] Wallet ledger and in-app shop purchase both work.
- [ ] Global cumulative leaderboard reads work.
- [ ] Self-learning feedback loop stores reviewable improvement rules only.
- [ ] Phase-2 items remain explicitly unimplemented.
