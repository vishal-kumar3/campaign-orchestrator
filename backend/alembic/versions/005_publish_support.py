"""publish support

Revision ID: 005_publish_support
Revises: 004_campaign_execution
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_publish_support"
down_revision: Union[str, Sequence[str], None] = "004_campaign_execution"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.execute("ALTER TYPE content_status ADD VALUE IF NOT EXISTS 'published'")
  op.execute("ALTER TYPE content_status ADD VALUE IF NOT EXISTS 'failed'")
  op.add_column(
    "campaign_contents",
    sa.Column("external_post_id", sa.Text(), nullable=True),
  )
  op.add_column(
    "campaign_contents",
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
  )


def downgrade() -> None:
  op.drop_column("campaign_contents", "published_at")
  op.drop_column("campaign_contents", "external_post_id")
  # PostgreSQL does not support removing enum values without recreating the type.
