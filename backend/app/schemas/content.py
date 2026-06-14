import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import ContentPlatform, ContentStatus


class ContentCreate(BaseModel):
  platform: ContentPlatform
  title: str | None = None
  content: str = Field(min_length=1)
  status: ContentStatus | None = None


class ContentUpdate(BaseModel):
  platform: ContentPlatform | None = None
  title: str | None = None
  content: str | None = Field(default=None, min_length=1)
  status: ContentStatus | None = None


class ContentResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  campaign_id: uuid.UUID
  platform: ContentPlatform
  title: str | None
  content: str
  status: ContentStatus
  created_at: datetime
  updated_at: datetime
