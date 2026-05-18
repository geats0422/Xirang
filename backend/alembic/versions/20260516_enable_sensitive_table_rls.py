"""enable RLS on sensitive public tables

Revision ID: 20260516_sensitive_rls
Revises: 20260515_creem_fields
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260516_sensitive_rls"
down_revision: Union[str, Sequence[str], None] = "20260515_creem_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SENSITIVE_TABLES = (
    "audit_logs",
    "auth_credentials",
    "auth_identities",
    "auth_sessions",
    "email_verification_codes",
    "payment_transactions",
    "purchase_records",
    "users",
    "wallet_ledger",
    "wallets",
)


def upgrade() -> None:
    for table_name in SENSITIVE_TABLES:
        op.execute(f'ALTER TABLE public."{table_name}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    for table_name in reversed(SENSITIVE_TABLES):
        op.execute(f'ALTER TABLE public."{table_name}" DISABLE ROW LEVEL SECURITY')
