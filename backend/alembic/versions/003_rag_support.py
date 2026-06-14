"""rag support

Revision ID: 003_rag_support
Revises: 002_initial_schema
Create Date: 2026-06-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_rag_support"
down_revision: Union[str, Sequence[str], None] = "002_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))
  op.execute(
    "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
    "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
  )


def downgrade() -> None:
  op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
  op.drop_column("documents", "processing_error")
