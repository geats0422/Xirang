# Xirang Backend Phase 1 Scope Lock

> This document defines the **exact scope** for Phase 1 backend development.
> Any feature not listed here is **out of scope** and must be deferred to Phase 2.

## Phase 1 Must Have

### Authentication
- [x] Email/password registration
- [x] Email/password login
- [x] JWT access token + refresh token
- [x] Server-side refresh token session management
- [x] Token refresh endpoint
- [x] Logout (revoke refresh token)
- [x] Get current user profile

### Documents
- [x] Upload PDF/DOCX/TXT/Markdown files
- [x] Immediate visibility with `processing` status
- [x] Document list for current user
- [x] Document detail view
- [x] Document status query
- [x] Retry failed documents
- [x] Delete document (soft delete)

### Document Processing (Worker)
- [x] File parsing (PDF, DOCX, TXT, MD)
- [x] PageIndex indexing
- [x] Base question bank generation
- [x] Document status transitions: `processing` -> `ready` or `failed`

### Question Bank
- [x] Single choice questions
- [x] Multiple choice questions
- [x] True/false questions
- [x] Questions linked to documents

### Game Modes (Unified Run Flow)
- [x] Create run from document (any of 3 modes)
- [x] Get run questions
- [x] Submit answers
- [x] Run completion

### Settlement
- [x] Rule-based XP calculation
- [x] Rule-based coins calculation
- [x] Combo multiplier
- [x] Deterministic, testable formulas
- [x] NO AI involvement in reward values

### Wallet & Economy
- [x] Wallet balance view (computed from ledger)
- [x] Transaction ledger writes
- [x] Transaction history

### Shop (Minimum Viable)
- [x] List purchasable items
- [x] Purchase with coins
- [x] Deduct coins from wallet
- [x] Write ledger entry
- [x] Increment user inventory

### Leaderboard
- [x] Global cumulative leaderboard (read-only)
- [x] Sorted by total XP

### Review & Feedback
- [x] View mistakes for completed runs
- [x] Mistake embeddings (pgvector)
- [x] Similar mistake recall
- [x] Enhanced mistake explanation
- [x] Submit "this question is wrong" feedback
- [x] Feedback persistence

### Self-Learning (Worker)
- [x] Feedback aggregation
- [x] Self-learning agent summarization
- [x] Write improvement suggestions to reviewable rule repository
- [x] Rules stored for human review, NOT auto-applied

### Profile & Settings
- [x] Get/update user profile
- [x] Get/update user settings

### Document AI Features
- [x] Ask question about current document only
- [x] Study recommendations (sections + reasons + next steps)

### Infrastructure
- [x] Local PostgreSQL database
- [x] Local filesystem storage
- [x] Separate worker process
- [x] Job table for background tasks
- [x] Alembic migrations

---

## Phase 1 Must NOT Have (Guardrails)

### Authentication
- [ ] OAuth (Google, GitHub, Microsoft)
- [ ] Account deletion/soft delete endpoint
- [ ] Password reset via email
- [ ] Email verification

### Documents
- [ ] Fill-in-the-blank question generation
- [ ] Cross-document search
- [ ] Document sharing
- [ ] Document versioning

### Game & Settlement
- [ ] Weekly seasons
- [ ] Division/rank promotion
- [ ] Quest system
- [ ] Achievement badges

### Economy
- [ ] Real payment gateway
- [ ] Subscription billing
- [ ] Refund processing
- [ ] External currency conversion

### AI & Retrieval
- [ ] Cross-document Q&A
- [ ] Multi-model switching (user-facing)
- [ ] Ollama integration
- [ ] Model pool configuration

### Infrastructure
- [ ] Celery/Redis queue system
- [ ] Object storage (S3) - only seam exists
- [ ] Supabase-specific features
- [ ] Horizontal scaling

### Self-Learning
- [ ] Auto-apply generated rules
- [ ] Auto-modify prompts
- [ ] Auto-update question bank

---

## File Size & Retry Defaults

| Setting | Value |
|---------|-------|
| Max file size (hard limit) | 50 MB |
| Recommended file size | <= 20 MB |
| Max retry attempts | 3 |
| Retry backoff | Exponential |
| Local upload directory | `backend/.data/uploads/` |

---

## Timezone Baseline

- Default timezone for season logic: `Asia/Shanghai`
- Configurable via environment variable

---

## Technology Constraints

### Required
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL 15+ with pgvector
- Alembic
- OpenAI Agents SDK
- Self-hosted PageIndex

### Forbidden in Phase 1
- Celery
- Redis (as message broker)
- AWS/GCP/Azure specific SDKs
- OAuth client libraries
- Payment gateway SDKs

---

## Verification Checklist

Before considering Phase 1 complete:

- [ ] All "Must Have" items are implemented
- [ ] No "Must NOT Have" items are implemented
- [ ] All tests pass (unit, integration, E2E)
- [ ] Lint and type checks pass
- [ ] Local smoke run documented
- [ ] Phase 2 follow-ups tracked

---

## Phase 2 Preview

The following are **explicitly deferred** to Phase 2:

1. OAuth providers (Google, GitHub, Microsoft)
2. Real payment integration
3. Subscription billing
4. Weekly seasons and promotion logic
5. Quest/achievement backend
6. Multi-model switching
7. Ollama support
8. Fill-in-the-blank questions
9. Account deletion
10. Cross-document Q&A
11. Celery/Redis upgrade (optional)

See `docs/backend-phase2-followups.md` (to be created in Task 14) for detailed Phase 2 planning.
