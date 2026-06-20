import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResearchSnapshotResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  campaign_id: uuid.UUID
  summary: str | None
  raw_data: dict | None
  created_at: datetime
