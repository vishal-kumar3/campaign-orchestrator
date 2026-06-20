import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.config import settings
from app.db.models.enums import CampaignStatus, ContentPlatform


class CampaignCreate(BaseModel):
  title: str = Field(min_length=1, max_length=255)
  objective: str = Field(min_length=1)
  target_audience: str | None = None
  region: str | None = None
  platforms: list[ContentPlatform] | None = None
  knowledge_base_id: uuid.UUID | None = None
  competitor_urls: list[Annotated[str, HttpUrl]] | None = None

  @field_validator("competitor_urls")
  @classmethod
  def validate_competitor_urls(
    cls, value: list[Annotated[str, HttpUrl]] | None
  ) -> list[Annotated[str, HttpUrl]] | None:
    if value is not None and len(value) > settings.agent_max_competitor_urls:
      raise ValueError(
        f"At most {settings.agent_max_competitor_urls} competitor URLs allowed"
      )
    return value


class CampaignUpdate(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=255)
  objective: str | None = Field(default=None, min_length=1)
  target_audience: str | None = None
  region: str | None = None
  platforms: list[ContentPlatform] | None = None
  status: CampaignStatus | None = None
  knowledge_base_id: uuid.UUID | None = None
  competitor_urls: list[Annotated[str, HttpUrl]] | None = None

  @field_validator("competitor_urls")
  @classmethod
  def validate_competitor_urls(
    cls, value: list[Annotated[str, HttpUrl]] | None
  ) -> list[Annotated[str, HttpUrl]] | None:
    if value is not None and len(value) > settings.agent_max_competitor_urls:
      raise ValueError(
        f"At most {settings.agent_max_competitor_urls} competitor URLs allowed"
      )
    return value


class CampaignResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  workspace_id: uuid.UUID
  title: str
  objective: str
  target_audience: str | None
  region: str | None
  platforms: list[ContentPlatform] | None
  knowledge_base_id: uuid.UUID | None
  competitor_urls: list[str] | None
  status: CampaignStatus
  created_at: datetime
  updated_at: datetime
