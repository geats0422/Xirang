from collections.abc import Sequence


revision: str = "13210a3f6138"
down_revision: str | Sequence[str] | None = (
    "20260409_add_quest_tables",
    "53c6b1672747_add_learning_paths",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
