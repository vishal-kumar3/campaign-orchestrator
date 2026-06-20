import uuid
from typing import Literal

from pydantic import BaseModel, Field
from datetime import datetime

from app.db.models.enums import CampaignStatus


class ContentApprovalItem(BaseModel):
  id: uuid.UUID
  content: str | None = Field(default=None, min_length=1)
  status: Literal["approved", "rejected"]
  scheduled_at: datetime | None = None


class ApproveCampaignRequest(BaseModel):
  contents: list[ContentApprovalItem] = Field(min_length=1)
  reject_all_to_draft: bool = False


class ApproveCampaignResponse(BaseModel):
  campaign_id: uuid.UUID
  status: CampaignStatus
  approved_count: int
  rejected_count: int
  resuming: bool
