# Xirang Backend

FastAPI backend for the Xirang gamified learning platform.

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL + pgvector
- **Migrations**: Alembic
- **AI**: OpenAI Agents SDK, self-hosted PageIndex
- **Testing**: pytest + httpx

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- (Optional) PageIndex self-hosted instance

### Setup

1. Create virtual environment:
```bash
cd backend
uv venv .venv
```

2. Install dependencies:
```bash
uv sync --extra dev
```

3. Copy environment config:
```bash
cp .env.example .env
# Edit .env with your local settings
```

4. Initialize database:
```bash
uv run python ../scripts/init_db.py

# If pgvector is not installed locally yet:
uv run python ../scripts/init_db.py --skip-vector-extension
```

5. Run migrations:
```bash
uv run alembic upgrade head
```

6. Configure PageIndex child-service startup for local development (recommended):
```bash
# Example: replace with your real PageIndex startup command
PAGEINDEX_LAUNCH_COMMAND="pageindex serve --host {host} --port {port} --log-level {log_level}"
```

Available placeholders in `PAGEINDEX_LAUNCH_COMMAND`:
- `{host}`
- `{port}`
- `{url}`
- `{log_level}`

If `PAGEINDEX_LAUNCH_COMMAND` is empty and `PAGEINDEX_MOCK_FALLBACK=true`, backend will fall back to the in-repo mock PageIndex server for local development.

7. Start development server:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── api/                 # API routes
│   │   ├── router.py
│   │   └── v1/
│   ├── core/                # Config, logging, security
│   ├── db/                  # Database models and session
│   ├── schemas/             # Pydantic schemas
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   ├── integrations/        # External service clients
│   └── workers/             # Background job workers
├── tests/
├── alembic/
├── alembic.ini
├── pyproject.toml
└── .env.example
```

## Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Lint
uv run ruff check app tests

# Type check
uv run mypy app

# Format
uv run ruff format app tests

# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
```

## Phase 1 Scope

See [docs/backend-phase1-scope.md](../docs/backend-phase1-scope.md) for the complete Phase 1 scope definition.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `PAGEINDEX_URL` | Self-hosted PageIndex URL | `http://localhost:8080` |
| `PAGEINDEX_LAUNCH_COMMAND` | Local child-process command used to auto-start real PageIndex | None |
| `PAGEINDEX_MOCK_FALLBACK` | Fall back to in-repo mock PageIndex when no real launch command is configured | `true` |
| `STORAGE_MODE` | Storage backend: `local` or `s3` | `local` |
| `UPLOAD_DIR` | Local upload directory | `.data/uploads` |

## License

MIT
