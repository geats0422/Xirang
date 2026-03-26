from typing import Sequence, Union

from alembic import op

revision: str = "8c7f9a21d4f0"
down_revision: Union[str, Sequence[str], None] = "5f1feb885f66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documentformat")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS ck_documents_documentformat")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS ck_documents_format")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_format_check")
    op.execute(
        """
        ALTER TABLE documents
        ADD CONSTRAINT documentformat
        CHECK (format IN ('pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'markdown'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documentformat")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS ck_documents_documentformat")
    op.execute(
        """
        ALTER TABLE documents
        ADD CONSTRAINT documentformat
        CHECK (format IN ('pdf', 'docx', 'txt', 'markdown'))
        """
    )
