import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import CampaignStatus, ContentPlatform


class CampaignCreate(BaseModel):
  title: str = Field(min_length=1, max_length=255)
  objective: str = Field(min_length=1)
  target_audience: str | None = None
  region: str | None = None
  platforms: list[ContentPlatform] | None = None


class CampaignUpdate(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=255)
  objective: str | None = Field(default=None, min_length=1)
  target_audience: str | None = None
  region: str | None = None
  platforms: list[ContentPlatform] | None = None
  status: CampaignStatus | None = None


class CampaignResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  workspace_id: uuid.UUID
  title: str
  objective: str
  target_audience: str | None
  region: str | None
  platforms: list[ContentPlatform] | None
  status: CampaignStatus
  created_at: datetime
  updated_at: datetime
