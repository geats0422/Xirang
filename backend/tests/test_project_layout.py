"""Project layout verification tests."""

from pathlib import Path


def test_backend_directory_exists():
    """Verify backend directory exists."""
    backend_dir = Path(__file__).parent.parent
    assert backend_dir.exists()
    assert backend_dir.name == "backend"


def test_app_package_exists():
    """Verify app package exists."""
    app_dir = Path(__file__).parent.parent / "app"
    assert app_dir.exists()
    assert (app_dir / "__init__.py").exists()


def test_tests_package_exists():
    """Verify tests package exists."""
    tests_dir = Path(__file__).parent
    assert tests_dir.exists()
    assert (tests_dir / "__init__.py").exists()


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists with required dependencies."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_path.exists()

    content = pyproject_path.read_text()
    assert "fastapi" in content
    assert "sqlalchemy" in content
    assert "alembic" in content
    assert "pytest" in content


def test_env_example_exists():
    """Verify .env.example exists with required variables."""
    env_example_path = Path(__file__).parent.parent / ".env.example"
    assert env_example_path.exists()

    content = env_example_path.read_text()
    assert "DATABASE_URL" in content
    assert "SECRET_KEY" in content
    assert "OPENAI_API_KEY" in content


def test_phase1_scope_doc_exists():
    """Verify Phase 1 scope document exists."""
    scope_doc_path = Path(__file__).parent.parent.parent / "docs" / "backend-phase1-scope.md"
    assert scope_doc_path.exists()

    content = scope_doc_path.read_text()
    assert "Phase 1" in content or "phase-1" in content.lower()


def test_readme_exists():
    """Verify backend README exists."""
    readme_path = Path(__file__).parent.parent / "README.md"
    assert readme_path.exists()

    content = readme_path.read_text(encoding="utf-8")
    assert "FastAPI" in content
    assert "pytest" in content
