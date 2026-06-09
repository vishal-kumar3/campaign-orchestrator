import uuid
from datetime import datetime

from app.db.models.enums import AgentStatus, enum_values
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentRun(Base):
  __tablename__ = "agent_runs"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  campaign_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
  )

  agent_name: Mapped[str] = mapped_column(Text, nullable=False)

  status: Mapped[AgentStatus] = mapped_column(
    Enum(
      AgentStatus,
      name="agent_status",
      values_callable=enum_values,
      create_constraint=True,
    ),
    server_default=text("'running'"),
  )

  input: Mapped[dict | None] = mapped_column(JSONB)
  output: Mapped[dict | None] = mapped_column(JSONB)

  started_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )
  completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

  # Relationships
  campaign: Mapped["Campaign"] = relationship(back_populates="agent_runs")
  logs: Mapped[list["AgentLog"]] = relationship(
    back_populates="run", cascade="all, delete-orphan"
  )
