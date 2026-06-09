import uuid
from datetime import datetime

from app.db.models.enums import KnowledgeScope, enum_values
from sqlalchemy import DateTime, Enum, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KnowledgeBase(Base):
  __tablename__ = "knowledge_bases"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  workspace_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
  )
  # No FK constraint added here to match your SQL and avoid circular dependency issues during table creation
  campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

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
  documents: Mapped[list["Document"]] = relationship(
    back_populates="knowledge_base", cascade="all, delete-orphan"
  )
