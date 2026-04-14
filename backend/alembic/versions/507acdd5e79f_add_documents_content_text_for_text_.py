from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "507acdd5e79f"
down_revision: Union[str, Sequence[str], None] = "e2fae03e8983"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("content_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "content_text")
