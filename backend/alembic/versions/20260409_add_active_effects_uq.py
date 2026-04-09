from collections.abc import Sequence

from alembic import op

revision: str = "20260409_add_active_effects_uq"
down_revision: str | Sequence[str] | None = "20260408_shop_effects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_active_effects_user_type",
        "active_effects",
        ["user_id", "effect_type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_active_effects_user_type", "active_effects", type_="unique")
