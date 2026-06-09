import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchSnapshot(Base):
  __tablename__ = "research_snapshots"
  __table_args__ = (Index("ix_research_snapshots_campaign_id", "campaign_id"),)

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  campaign_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
  )

  summary: Mapped[str | None] = mapped_column(Text)
  raw_data: Mapped[dict | None] = mapped_column(JSONB)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  campaign: Mapped["Campaign"] = relationship(back_populates="research_snapshots")
