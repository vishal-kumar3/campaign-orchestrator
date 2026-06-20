import uuid
from datetime import datetime

from app.db.models.enums import ContentPlatform, ContentStatus, enum_values
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CampaignContent(Base):
  __tablename__ = "campaign_contents"
  __table_args__ = (
    Index("ix_campaign_contents_campaign_id", "campaign_id"),
    Index("ix_campaign_contents_campaign_platform_variant", "campaign_id", "platform", "variant"),
  )

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  campaign_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
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
  title: Mapped[str | None] = mapped_column(Text)
  content: Mapped[str] = mapped_column(Text, nullable=False)

  status: Mapped[ContentStatus] = mapped_column(
    Enum(
      ContentStatus,
      name="content_status",
      values_callable=enum_values,
      create_constraint=True,
    ),
    server_default=text("'draft'"),
  )

  external_post_id: Mapped[str | None] = mapped_column(Text)
  published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

  variant: Mapped[str] = mapped_column(String(10), server_default=text("'A'"))
  scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
  engagement_metrics: Mapped[dict] = mapped_column(
    JSONB, server_default=text("'{}'::jsonb")
  )

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )

  # Relationships
  campaign: Mapped["Campaign"] = relationship(back_populates="contents")
  scheduled_jobs: Mapped[list["ScheduledJob"]] = relationship(
    back_populates="content", cascade="all, delete-orphan"
  )
