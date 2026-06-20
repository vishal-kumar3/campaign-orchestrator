import uuid
from datetime import datetime

from app.db.models.enums import CampaignStatus, ContentPlatform, enum_values
from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Campaign(Base):
  __tablename__ = "campaigns"
  __table_args__ = (Index("ix_campaigns_workspace_id", "workspace_id"),)

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  workspace_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
  )

  title: Mapped[str] = mapped_column(String(255), nullable=False)
  objective: Mapped[str] = mapped_column(Text, nullable=False)
  target_audience: Mapped[str | None] = mapped_column(Text)
  region: Mapped[str | None] = mapped_column(Text)
  platforms: Mapped[list[ContentPlatform] | None] = mapped_column(
    ARRAY(
      Enum(
        ContentPlatform,
        name="content_platform",
        values_callable=enum_values,
        create_constraint=False,
      )
    )
  )
  knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
    nullable=True,
  )
  competitor_urls: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

  status: Mapped[CampaignStatus] = mapped_column(
    Enum(
      CampaignStatus,
      name="campaign_status",
      values_callable=enum_values,
      create_constraint=True,
    ),
    server_default=text("'draft'"),
  )

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )

  # Relationships
  workspace: Mapped["Workspace"] = relationship(back_populates="campaigns")
  knowledge_base: Mapped["KnowledgeBase | None"] = relationship(
    foreign_keys=[knowledge_base_id],
  )
  knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
    back_populates="campaign",
    foreign_keys="KnowledgeBase.campaign_id",
  )
  research_snapshots: Mapped[list["ResearchSnapshot"]] = relationship(
    back_populates="campaign", cascade="all, delete-orphan"
  )
  contents: Mapped[list["CampaignContent"]] = relationship(
    back_populates="campaign", cascade="all, delete-orphan"
  )
  agent_runs: Mapped[list["AgentRun"]] = relationship(
    back_populates="campaign", cascade="all, delete-orphan"
  )
  workflow_threads: Mapped[list["WorkflowThread"]] = relationship(
    back_populates="campaign", cascade="all, delete-orphan"
  )
