import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Workspace(Base):
  __tablename__ = "workspaces"

  id: Mapped[uuid.UUID] = mapped_column(
    primary_key=True,
    default=uuid.uuid4,
  )

  owner_id: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
  )

  name: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
  )

  description: Mapped[str] = mapped_column(Text())

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
