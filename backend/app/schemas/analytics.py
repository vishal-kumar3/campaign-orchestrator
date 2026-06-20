import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.enums import ContentPlatform, ContentStatus


class ContentAnalyticsItem(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  content_id: uuid.UUID
  platform: ContentPlatform
  variant: str
  status: ContentStatus
  engagement_metrics: dict
  scheduled_at: datetime | None = None
  published_at: datetime | None = None
  external_post_id: str | None = None


class PlatformSummary(BaseModel):
  platform: ContentPlatform
  impressions: int
  engagements: int
  clicks: int
  engagement_rate: float
  ctr: float


class VariantComparison(BaseModel):
  platform: ContentPlatform
  variant_a_rate: float
  variant_b_rate: float
  winner: str


class CampaignAnalyticsResponse(BaseModel):
  campaign_id: uuid.UUID
  totals: dict
  by_platform: list[PlatformSummary]
  variants: list[VariantComparison]
  contents: list[ContentAnalyticsItem]
