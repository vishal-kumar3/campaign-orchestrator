import uuid
from datetime import datetime

from app.db.models.enums import ContentPlatform, enum_values
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EngagementHistory(Base):
  __tablename__ = "engagement_history"
  __table_args__ = (
    Index("ix_engagement_history_workspace_platform", "workspace_id", "platform"),
  )

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  workspace_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
  )
  platform: Mapped[ContentPlatform] = mapped_column(
    Enum(
      ContentPlatform,
      name="content_platform",
      values_callable=enum_values,
      create_constraint=True,
    ),
    nullable=False,
  )
  post_hour: Mapped[int] = mapped_column(Integer, nullable=False)
  post_day: Mapped[int] = mapped_column(Integer, nullable=False)
  post_type: Mapped[str] = mapped_column(Text, nullable=False)
  impressions: Mapped[int] = mapped_column(Integer, nullable=False)
  engagements: Mapped[int] = mapped_column(Integer, nullable=False)
  clicks: Mapped[int] = mapped_column(Integer, nullable=False)
  recorded_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )
