"""phase 4 scale

Revision ID: 006_phase4_scale
Revises: 005_publish_support
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_phase4_scale"
down_revision: Union[str, Sequence[str], None] = "005_publish_support"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

content_platform = postgresql.ENUM(
  "twitter",
  "linkedin",
  "email",
  "blog",
  name="content_platform",
  create_type=False,
)


def upgrade() -> None:
  op.add_column(
    "campaign_contents",
    sa.Column("variant", sa.String(length=10), server_default="A", nullable=False),
  )
  op.add_column(
    "campaign_contents",
    sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
  )
  op.add_column(
    "campaign_contents",
    sa.Column(
      "engagement_metrics",
      postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
  )
  op.create_index(
    "ix_campaign_contents_campaign_platform_variant",
    "campaign_contents",
    ["campaign_id", "platform", "variant"],
  )

  op.create_table(
    "scheduled_jobs",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("content_id", sa.UUID(), nullable=True),
    sa.Column("document_id", sa.UUID(), nullable=True),
    sa.Column("celery_task_id", sa.Text(), nullable=True),
    sa.Column("job_type", sa.Text(), nullable=False),
    sa.Column("status", sa.Text(), server_default="pending", nullable=False),
    sa.Column("execute_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
    sa.Column("last_error", sa.Text(), nullable=True),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(
      ["content_id"],
      ["campaign_contents.id"],
      ondelete="CASCADE",
    ),
    sa.ForeignKeyConstraint(
      ["document_id"],
      ["documents.id"],
      ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("ix_scheduled_jobs_content_id", "scheduled_jobs", ["content_id"])
  op.create_index("ix_scheduled_jobs_execute_at", "scheduled_jobs", ["execute_at"])
  op.execute(
    """
    CREATE UNIQUE INDEX uq_scheduled_jobs_active_publish
    ON scheduled_jobs (content_id)
    WHERE job_type = 'publish' AND status IN ('pending', 'running')
    """
  )

  op.create_table(
    "engagement_history",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("workspace_id", sa.UUID(), nullable=False),
    sa.Column("platform", content_platform, nullable=False),
    sa.Column("post_hour", sa.Integer(), nullable=False),
    sa.Column("post_day", sa.Integer(), nullable=False),
    sa.Column("post_type", sa.Text(), nullable=False),
    sa.Column("impressions", sa.Integer(), nullable=False),
    sa.Column("engagements", sa.Integer(), nullable=False),
    sa.Column("clicks", sa.Integer(), nullable=False),
    sa.Column(
      "recorded_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index(
    "ix_engagement_history_workspace_platform",
    "engagement_history",
    ["workspace_id", "platform"],
  )


def downgrade() -> None:
  op.drop_index("ix_engagement_history_workspace_platform", table_name="engagement_history")
  op.drop_table("engagement_history")
  op.execute("DROP INDEX IF EXISTS uq_scheduled_jobs_active_publish")
  op.drop_index("ix_scheduled_jobs_execute_at", table_name="scheduled_jobs")
  op.drop_index("ix_scheduled_jobs_content_id", table_name="scheduled_jobs")
  op.drop_table("scheduled_jobs")
  op.drop_index(
    "ix_campaign_contents_campaign_platform_variant",
    table_name="campaign_contents",
  )
  op.drop_column("campaign_contents", "engagement_metrics")
  op.drop_column("campaign_contents", "scheduled_at")
  op.drop_column("campaign_contents", "variant")
