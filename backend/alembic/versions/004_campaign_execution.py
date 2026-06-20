"""campaign execution support

Revision ID: 004_campaign_execution
Revises: 003_rag_support
Create Date: 2026-06-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_campaign_execution"
down_revision: Union[str, Sequence[str], None] = "003_rag_support"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.add_column(
    "campaigns",
    sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=True),
  )
  op.add_column(
    "campaigns",
    sa.Column("competitor_urls", postgresql.ARRAY(sa.Text()), nullable=True),
  )
  op.create_foreign_key(
    "fk_campaigns_knowledge_base_id",
    "campaigns",
    "knowledge_bases",
    ["knowledge_base_id"],
    ["id"],
    ondelete="SET NULL",
  )
  op.create_index(
    "ix_campaigns_knowledge_base_id",
    "campaigns",
    ["knowledge_base_id"],
    unique=False,
    postgresql_where=sa.text("knowledge_base_id IS NOT NULL"),
  )


def downgrade() -> None:
  op.drop_index("ix_campaigns_knowledge_base_id", table_name="campaigns")
  op.drop_constraint("fk_campaigns_knowledge_base_id", "campaigns", type_="foreignkey")
  op.drop_column("campaigns", "competitor_urls")
  op.drop_column("campaigns", "knowledge_base_id")
