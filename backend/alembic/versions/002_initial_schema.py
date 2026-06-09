"""initial schema

Revision ID: 002_initial_schema
Revises: 001_enable_pgvector
Create Date: 2026-06-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "002_initial_schema"
down_revision: Union[str, Sequence[str], None] = "001_enable_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UPDATED_AT_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def _create_updated_at_trigger(table_name: str) -> None:
  op.execute(
    f"""
    CREATE TRIGGER trg_{table_name}_updated_at
    BEFORE UPDATE ON {table_name}
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
    """
  )


def upgrade() -> None:
  op.create_table(
    "workspaces",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("owner_id", sa.String(length=255), nullable=False),
    sa.Column("name", sa.String(length=255), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.Column(
      "updated_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("id"),
  )

  op.create_table(
    "campaigns",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("workspace_id", sa.UUID(), nullable=False),
    sa.Column("title", sa.String(length=255), nullable=False),
    sa.Column("objective", sa.Text(), nullable=False),
    sa.Column("target_audience", sa.Text(), nullable=True),
    sa.Column("region", sa.Text(), nullable=True),
    sa.Column(
      "platforms",
      sa.ARRAY(
        sa.Enum(
          "twitter",
          "linkedin",
          "email",
          "blog",
          name="content_platform",
          create_constraint=True,
        )
      ),
      nullable=True,
    ),
    sa.Column(
      "status",
      sa.Enum(
        "draft",
        "researching",
        "generating",
        "approval_pending",
        "completed",
        "failed",
        name="campaign_status",
        create_constraint=True,
      ),
      server_default=sa.text("'draft'"),
      nullable=False,
    ),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.Column(
      "updated_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("ix_campaigns_workspace_id", "campaigns", ["workspace_id"])

  op.create_table(
    "knowledge_bases",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("workspace_id", sa.UUID(), nullable=False),
    sa.Column("campaign_id", sa.UUID(), nullable=True),
    sa.Column(
      "scope",
      sa.Enum("workspace", "campaign", name="knowledge_scope", create_constraint=True),
      nullable=False,
    ),
    sa.Column("name", sa.String(length=255), nullable=False),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.CheckConstraint(
      "(scope = 'workspace' AND campaign_id IS NULL) OR "
      "(scope = 'campaign' AND campaign_id IS NOT NULL)",
      name="ck_knowledge_bases_scope_campaign_id",
    ),
    sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index(
    "ix_knowledge_bases_workspace_id", "knowledge_bases", ["workspace_id"]
  )
  op.create_index(
    "ix_knowledge_bases_campaign_id",
    "knowledge_bases",
    ["campaign_id"],
    postgresql_where=sa.text("campaign_id IS NOT NULL"),
  )

  op.create_table(
    "documents",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("knowledge_base_id", sa.UUID(), nullable=False),
    sa.Column("file_name", sa.Text(), nullable=False),
    sa.Column("file_url", sa.Text(), nullable=False),
    sa.Column("mime_type", sa.Text(), nullable=True),
    sa.Column(
      "status",
      sa.Enum(
        "pending",
        "processing",
        "indexed",
        "failed",
        name="document_status",
        create_constraint=True,
      ),
      server_default=sa.text("'pending'"),
      nullable=False,
    ),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(
      ["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"
    ),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index(
    "ix_documents_knowledge_base_id", "documents", ["knowledge_base_id"]
  )

  op.create_table(
    "document_chunks",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("document_id", sa.UUID(), nullable=False),
    sa.Column("chunk_index", sa.Integer(), nullable=False),
    sa.Column("content", sa.Text(), nullable=False),
    sa.Column("embedding", Vector(1536), nullable=True),
    sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint(
      "document_id",
      "chunk_index",
      name="uq_document_chunks_document_chunk_index",
    ),
  )
  op.create_index(
    "ix_document_chunks_document_id", "document_chunks", ["document_id"]
  )

  op.create_table(
    "research_snapshots",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("campaign_id", sa.UUID(), nullable=False),
    sa.Column("summary", sa.Text(), nullable=True),
    sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index(
    "ix_research_snapshots_campaign_id", "research_snapshots", ["campaign_id"]
  )

  op.create_table(
    "campaign_contents",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("campaign_id", sa.UUID(), nullable=False),
    sa.Column(
      "platform",
      sa.Enum(
        "twitter",
        "linkedin",
        "email",
        "blog",
        name="content_platform",
        create_type=False,
        create_constraint=True,
      ),
      nullable=False,
    ),
    sa.Column("title", sa.Text(), nullable=True),
    sa.Column("content", sa.Text(), nullable=False),
    sa.Column(
      "status",
      sa.Enum(
        "draft",
        "approved",
        "rejected",
        name="content_status",
        create_constraint=True,
      ),
      server_default=sa.text("'draft'"),
      nullable=False,
    ),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.Column(
      "updated_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index(
    "ix_campaign_contents_campaign_id", "campaign_contents", ["campaign_id"]
  )

  op.create_table(
    "agent_runs",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("campaign_id", sa.UUID(), nullable=False),
    sa.Column("agent_name", sa.Text(), nullable=False),
    sa.Column(
      "status",
      sa.Enum(
        "running",
        "completed",
        "failed",
        name="agent_status",
        create_constraint=True,
      ),
      server_default=sa.text("'running'"),
      nullable=False,
    ),
    sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column(
      "started_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("ix_agent_runs_campaign_id", "agent_runs", ["campaign_id"])

  op.create_table(
    "agent_logs",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("run_id", sa.UUID(), nullable=False),
    sa.Column("node_name", sa.Text(), nullable=False),
    sa.Column(
      "level",
      sa.Enum("info", "warning", "error", name="log_level", create_constraint=True),
      server_default=sa.text("'info'"),
      nullable=False,
    ),
    sa.Column("message", sa.Text(), nullable=False),
    sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("ix_agent_logs_run_id", "agent_logs", ["run_id"])

  op.create_table(
    "workflow_threads",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("campaign_id", sa.UUID(), nullable=False),
    sa.Column("thread_id", sa.Text(), nullable=False),
    sa.Column("status", sa.Text(), nullable=True),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index(
    "ix_workflow_threads_campaign_id", "workflow_threads", ["campaign_id"]
  )
  op.create_index(
    "ix_workflow_threads_thread_id", "workflow_threads", ["thread_id"], unique=True
  )

  op.execute(UPDATED_AT_TRIGGER_FUNCTION)
  for table in ("workspaces", "campaigns", "campaign_contents"):
    _create_updated_at_trigger(table)


def downgrade() -> None:
  for table in ("campaign_contents", "campaigns", "workspaces"):
    op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
  op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

  op.drop_table("workflow_threads")
  op.drop_table("agent_logs")
  op.drop_table("agent_runs")
  op.drop_table("campaign_contents")
  op.drop_table("research_snapshots")
  op.drop_table("document_chunks")
  op.drop_table("documents")
  op.drop_table("knowledge_bases")
  op.drop_table("campaigns")
  op.drop_table("workspaces")

  op.execute("DROP TYPE IF EXISTS log_level")
  op.execute("DROP TYPE IF EXISTS agent_status")
  op.execute("DROP TYPE IF EXISTS content_status")
  op.execute("DROP TYPE IF EXISTS content_platform")
  op.execute("DROP TYPE IF EXISTS document_status")
  op.execute("DROP TYPE IF EXISTS knowledge_scope")
  op.execute("DROP TYPE IF EXISTS campaign_status")
