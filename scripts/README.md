# Xirang Scripts

Utility scripts for database initialization and maintenance.

## init_db.py

Initialize the local PostgreSQL database for development.

### Prerequisites

- PostgreSQL 15+ installed and running
- `pgvector` extension available
- Database user with CREATE DATABASE and CREATE EXTENSION privileges

### Usage

```bash
# Show help
uv run python scripts/init_db.py --help

# Initialize with default settings (from .env)
uv run python scripts/init_db.py

# Initialize with custom database URL
uv run python scripts/init_db.py --database-url "postgresql://user:pass@localhost:5432/xirang"

# Drop and recreate (DESTRUCTIVE)
uv run python scripts/init_db.py --reset

# Skip pgvector bootstrap when the extension is not installed yet
uv run python scripts/init_db.py --skip-vector-extension
```

### What it does

1. Creates the database if it doesn't exist
2. Enables the `pgvector` extension
3. Runs Alembic migrations to latest version
4. Verifies the setup with a smoke query

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |

## Future Scripts

Additional scripts will be added as needed:

- `seed_demo_data.py` - Populate database with demo content
- `cleanup_jobs.py` - Remove completed/failed job records
- `export_analytics.py` - Export usage analytics

## Notes

- All scripts should be run from the repository root
- Scripts use the same environment configuration as the backend
- Scripts are designed for local development, not production use
