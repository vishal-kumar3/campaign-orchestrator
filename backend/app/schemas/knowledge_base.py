import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models.enums import KnowledgeScope


class KnowledgeBaseCreate(BaseModel):
  name: str = Field(min_length=1, max_length=255)
  scope: KnowledgeScope
  campaign_id: uuid.UUID | None = None

  @model_validator(mode="after")
  def validate_scope_campaign_id(self) -> "KnowledgeBaseCreate":
    if self.scope == KnowledgeScope.WORKSPACE and self.campaign_id is not None:
      raise ValueError("campaign_id must be null when scope is workspace")
    if self.scope == KnowledgeScope.CAMPAIGN and self.campaign_id is None:
      raise ValueError("campaign_id is required when scope is campaign")
    return self


class KnowledgeBaseUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=255)
  scope: KnowledgeScope | None = None
  campaign_id: uuid.UUID | None = None

  @model_validator(mode="after")
  def validate_scope_campaign_id(self) -> "KnowledgeBaseUpdate":
    if self.scope is None and self.campaign_id is None:
      return self
    scope = self.scope
    campaign_id = self.campaign_id
    if scope == KnowledgeScope.WORKSPACE and campaign_id is not None:
      raise ValueError("campaign_id must be null when scope is workspace")
    if scope == KnowledgeScope.CAMPAIGN and campaign_id is None:
      raise ValueError("campaign_id is required when scope is campaign")
    return self


class KnowledgeBaseResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  workspace_id: uuid.UUID
  campaign_id: uuid.UUID | None
  scope: KnowledgeScope
  name: str
  created_at: datetime
