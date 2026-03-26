from typing import Sequence, Union

from alembic import op

revision: str = "9f42c6d1e8aa"
down_revision: Union[str, Sequence[str], None] = "8c7f9a21d4f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documentformat")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS ck_documents_documentformat")
    op.execute(
        """
        ALTER TABLE documents
        ADD CONSTRAINT ck_documents_documentformat
        CHECK (format IN ('pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'markdown'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS ck_documents_documentformat")
    op.execute(
        """
        ALTER TABLE documents
        ADD CONSTRAINT ck_documents_documentformat
        CHECK (format IN ('pdf', 'docx', 'txt', 'markdown'))
        """
    )
