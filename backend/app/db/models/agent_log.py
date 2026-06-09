import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentLog(Base):
  __tablename__ = "agent_logs"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  run_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
  )

  level: Mapped[str | None] = mapped_column(Text)
  message: Mapped[str | None] = mapped_column(Text)
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  run: Mapped["AgentRun"] = relationship(back_populates="logs")
