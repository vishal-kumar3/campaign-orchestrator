import uuid
from datetime import datetime

from app.db.models.enums import KnowledgeScope, enum_values
from sqlalchemy import (
  CheckConstraint,
  DateTime,
  Enum,
  ForeignKey,
  Index,
  String,
  func,
  text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KnowledgeBase(Base):
  __tablename__ = "knowledge_bases"
  __table_args__ = (
    CheckConstraint(
      "(scope = 'workspace' AND campaign_id IS NULL) OR "
      "(scope = 'campaign' AND campaign_id IS NOT NULL)",
      name="ck_knowledge_bases_scope_campaign_id",
    ),
    Index("ix_knowledge_bases_workspace_id", "workspace_id"),
    Index(
      "ix_knowledge_bases_campaign_id",
      "campaign_id",
      postgresql_where=text("campaign_id IS NOT NULL"),
    ),
  )

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  workspace_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
  )
  campaign_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("campaigns.id", ondelete="CASCADE"),
    nullable=True,
  )

  scope: Mapped[KnowledgeScope] = mapped_column(
    Enum(
      KnowledgeScope,
      name="knowledge_scope",
      values_callable=enum_values,
      create_constraint=True,
    ),
    nullable=False,
  )
  name: Mapped[str] = mapped_column(String(255), nullable=False)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  workspace: Mapped["Workspace"] = relationship(back_populates="knowledge_bases")
  campaign: Mapped["Campaign | None"] = relationship(
    back_populates="knowledge_bases",
    foreign_keys=[campaign_id],
  )
  documents: Mapped[list["Document"]] = relationship(
    back_populates="knowledge_base", cascade="all, delete-orphan"
  )
