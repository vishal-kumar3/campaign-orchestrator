import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Workspace(Base):
  __tablename__ = "workspaces"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()"),
  )

  owner_id: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
  )

  name: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
  )

  description: Mapped[str | None] = mapped_column(Text, nullable=True)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    onupdate=func.now(),
  )

  # Relationships
  knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
    back_populates="workspace", cascade="all, delete-orphan"
  )
  campaigns: Mapped[list["Campaign"]] = relationship(
    back_populates="workspace", cascade="all, delete-orphan"
  )
