import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import AgentStatus, LogLevel


class AgentRunResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  campaign_id: uuid.UUID
  agent_name: str
  status: AgentStatus
  input: dict | None
  output: dict | None
  started_at: datetime
  completed_at: datetime | None


class AgentLogResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True, populate_by_name=True)

  id: uuid.UUID
  run_id: uuid.UUID
  node_name: str
  level: LogLevel
  message: str
  metadata: dict | None = Field(default=None, validation_alias="metadata_")
  created_at: datetime
