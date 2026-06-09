import uuid
from datetime import datetime

from app.db.models.enums import LogLevel, enum_values
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentLog(Base):
  __tablename__ = "agent_logs"
  __table_args__ = (Index("ix_agent_logs_run_id", "run_id"),)

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  run_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
  )

  node_name: Mapped[str] = mapped_column(Text, nullable=False)
  level: Mapped[LogLevel] = mapped_column(
    Enum(
      LogLevel,
      name="log_level",
      values_callable=enum_values,
      create_constraint=True,
    ),
    nullable=False,
    server_default=text("'info'"),
  )
  message: Mapped[str] = mapped_column(Text, nullable=False)
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  run: Mapped["AgentRun"] = relationship(back_populates="logs")
