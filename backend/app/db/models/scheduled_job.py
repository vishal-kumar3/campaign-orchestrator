import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScheduledJob(Base):
  __tablename__ = "scheduled_jobs"
  __table_args__ = (
    Index("ix_scheduled_jobs_content_id", "content_id"),
    Index("ix_scheduled_jobs_execute_at", "execute_at"),
  )

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  content_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True), ForeignKey("campaign_contents.id", ondelete="CASCADE")
  )
  document_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE")
  )
  celery_task_id: Mapped[str | None] = mapped_column(Text)
  job_type: Mapped[str] = mapped_column(Text, nullable=False)
  status: Mapped[str] = mapped_column(Text, server_default=text("'pending'"))
  execute_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  retry_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
  last_error: Mapped[str | None] = mapped_column(Text)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  content: Mapped["CampaignContent | None"] = relationship(back_populates="scheduled_jobs")
