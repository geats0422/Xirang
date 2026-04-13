from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e2fae03e8983'
down_revision: Union[str, Sequence[str], None] = ('dc8e89e781a0', '20260410b901')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
