# AGENTS.md

This is a monorepo containing a Vue 3 frontend and FastAPI backend. Agentic coding tools should work in the appropriate subdirectory based on the task.

## Scope
- **Frontend**: `frontend/` — Vue 3 + TypeScript + Vite + Vue Router 4
- **Backend**: `backend/` — FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + pgvector
- **Tests**: Vitest (frontend), pytest (backend)
- **Global styles/tokens**: `frontend/src/styles/tokens.css`

## Rule Files
- No `.cursorrules`, `.cursor/rules/`, or `.github/copilot-instructions.md` files found.
- OpenCode internal config exists at `.opencode/AGENTS.md`.



## Communication Language
- **All replies must be in Chinese (中文)** unless the user explicitly requests otherwise in a non-Chinese language.
- This includes code comments, commit messages, documentation, and any written communication.

---

## Frontend (`frontend/`)

### Working Directory
Run all frontend commands from `D:\project\Xirang\frontend`.

### Commands
```bash
npm install           # Install dependencies
npm run dev           # Start dev server (http://localhost:5173)
npm run lint          # ESLint check (max-warnings=0)
npm run lint:fix      # ESLint with auto-fix
npm run typecheck     # vue-tsc --noEmit
npm run test          # vitest run --passWithNoTests
npm run build         # typecheck + vite build
```

### Single-Test Commands
```bash
# One test file
npm run test -- src/pages/DungeonScholarHomePage.spec.ts

# Multiple files
npm run test -- src/utils/auth.spec.ts src/components/GameSettlementModal.spec.ts

# By test name pattern
npm run test -- -t "clicking coin button navigates to shop"

# File + test name
npm run test -- src/pages/DungeonScholarSettingsPage.spec.ts -t "renders extracted settings sections"
```

### Project Structure
- `src/pages/` — Route-level Vue pages (PascalCase, feature-prefixed)
- `src/components/` — Reusable UI and feature components
- `src/components/layout/` — Shared layout (sidebar, etc.)
- `src/composables/` — Composition API logic (`useXxx.ts`)
- `src/constants/` — Shared constants (`routes.ts`)
- `src/router/` — Router setup with lazy-loaded pages
- `src/utils/` — Utility modules and auth helpers
- `src/api/` — HTTP client and API modules
- `public/` — Static assets

### Code Style (Frontend)
- **Imports**: ES modules only. Group: framework → shared app → local. Use relative imports (no path aliases).
- **Type imports**: `import { foo, type Bar }` where appropriate.
- **Vue SFC**: Use `<script setup lang="ts">`. Keep pages focused on composition; extract large visual sections to child components.
- **Formatting**: Double quotes, semicolons, trailing commas in multiline. Keep attributes compact in templates.
- **Types**: TypeScript strict mode. Explicit types for props, emits, complex arrays. Avoid `any`; prefer `unknown` with narrowing.
- **Naming**: Components `PascalCase.vue`, composables `useXxx.ts`, locals `camelCase`, CSS `kebab-case`.
- **Routes**: Use `ROUTES` from `src/constants/routes.ts`. Use `useRouteNavigation.ts` composable for navigation.
- **Styles**: Use tokens from `src/styles/tokens.css`. Prefer scoped styles. Extract heavy styling to child components.
- **Error handling**: Guard clauses and early returns. Fail closed for auth/storage. Avoid empty catch blocks.

### ESLint Rules (Frontend)
- `@typescript-eslint/no-unused-vars` is error (prefix with `_` to allow).
- `vue/multi-word-component-names` is disabled.
- Several template formatting rules disabled; don't reformat for non-existent Prettier rules.

### Testing (Frontend)
- Use `@vue/test-utils` with `createMemoryHistory()` + `createRouter()` for route-aware tests.
- Test behavior: navigation, events, conditional rendering.
- Keep `*.spec.ts` files near the code they test.

---

## Backend (`backend/`)

### Working Directory
Run all backend commands from `D:\project\Xirang\backend`.

### Commands
```bash
uv venv .venv                      # Create virtual environment
uv sync --extra dev                # Install dependencies
uv run alembic upgrade head        # Apply migrations
uv run uvicorn app.main:app --reload --port 8000  # Start dev server

# Quality checks
uv run ruff check app tests        # Lint
uv run ruff format app tests       # Format
uv run mypy app                    # Type check
uv run pytest tests -q --tb=short  # Run tests
uv run pytest --cov=app --cov-report=html  # Tests with coverage
```

### Single-Test Commands
```bash
# One test file
uv run pytest tests/api/test_auth_api.py -v

# Specific test function
uv run pytest tests/api/test_auth_api.py::test_register_endpoint_returns_created_auth_payload -v

# By pattern
uv run pytest tests/ -k "auth" -v

# Multiple files
uv run pytest tests/api/test_auth_api.py tests/api/test_system.py -q
```

### Project Structure
- `app/main.py` — FastAPI app factory
- `app/api/v1/` — API route handlers
- `app/core/` — Config, logging, security
- `app/db/` — Database models and session
- `app/schemas/` — Pydantic schemas
- `app/repositories/` — Data access layer
- `app/services/` — Business logic
- `app/integrations/` — External service clients (PageIndex, OpenAI)
- `app/workers/` — Background job workers
- `tests/` — Test files mirroring app structure

### Code Style (Backend)
- **Python version**: 3.11+
- **Line length**: 100 characters
- **Imports**: Use `isort` via ruff; `app` is known-first-party.
- **Types**: mypy strict mode. All functions need type hints.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes.
- **Async**: Use async/await throughout; SQLAlchemy async session.
- **Error handling**: Raise domain-specific exceptions from services; map to HTTP status in API layer.
- **Dependency injection**: Use FastAPI's `Depends()`; override in tests with `app.dependency_overrides`.

### Ruff Rules (Backend)
Enabled: E, F, I, N, W, UP, B, C4, SIM, TCH, RUF
Ignored: E501 (line length), B008 (function call in argument), TC003 (runtime type needed)

### Testing (Backend)
- Use `TestClient` from `fastapi.testclient` for API tests.
- Create fake service implementations and override dependencies.
- Test files in `tests/api/`, `tests/services/`, `tests/workers/` mirroring app structure.
- pytest asyncio mode is `auto`.

---

## Required Verification Before Finishing

### Frontend
- Small UI change: `lint` + `typecheck`
- Behavior change: `lint` + `typecheck` + targeted test(s)
- Structural/refactor: `lint` + `typecheck` + `test` + `build`

### Backend
- Small change: `ruff check` + `mypy app`
- Behavior change: `ruff check` + `mypy app` + targeted test(s)
- Structural/refactor: `ruff check` + `mypy app` + `pytest` + verify server starts

---

## Environment Variables

### Backend (`backend/.env`)
Key variables (see `backend/.env.example`):
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing key
- `OPENAI_API_KEY` — OpenAI API key
- `CORS_ORIGINS` — Comma-separated allowed origins

### Frontend (`frontend/.env`)
- `VITE_API_BASE_URL` — API base URL (empty = use Vite proxy)
- `VITE_API_PROXY_TARGET` — Dev proxy target (default: `http://localhost:8000`)

---

## Agent Guidance
- Prefer improving shared abstractions over copying logic.
- Search for existing components/composables/constants before creating new ones.
- Keep changes narrowly scoped and consistent with existing patterns.
- Do not add dependencies unless materially justified.
- Frontend and backend communicate via `/api/v1/*` endpoints (Vite proxy in dev).
- Update this file if you add new commands, workflows, or conventions.
