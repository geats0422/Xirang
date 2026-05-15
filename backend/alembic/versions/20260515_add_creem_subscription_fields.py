from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260515_creem_fields"
down_revision: Union[str, Sequence[str], None] = "20260515_email_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("subscription_status", sa.String(length=20), server_default="free", nullable=False))
    op.add_column("users", sa.Column("subscription_tier", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("creem_customer_id", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("creem_subscription_id", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("pricing_region", sa.String(length=20), server_default="standard", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "pricing_region")
    op.drop_column("users", "creem_subscription_id")
    op.drop_column("users", "creem_customer_id")
    op.drop_column("users", "subscription_expires_at")
    op.drop_column("users", "subscription_tier")
    op.drop_column("users", "subscription_status")
