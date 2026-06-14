import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
  name: str = Field(min_length=1, max_length=255)
  description: str | None = None


class WorkspaceUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=255)
  description: str | None = None


class WorkspaceResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  owner_id: str
  name: str
  description: str | None
  created_at: datetime
  updated_at: datetime
