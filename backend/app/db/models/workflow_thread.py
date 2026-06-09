import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowThread(Base):
  __tablename__ = "workflow_threads"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  campaign_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
  )

  thread_id: Mapped[str] = mapped_column(Text, nullable=False)
  status: Mapped[str | None] = mapped_column(Text)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  campaign: Mapped["Campaign"] = relationship(back_populates="workflow_threads")
