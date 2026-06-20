import uuid

from pydantic import BaseModel

from app.db.models.enums import CampaignStatus


class ExecuteCampaignResponse(BaseModel):
  campaign_id: uuid.UUID
  status: CampaignStatus
  thread_id: str
  message: str = "Campaign execution started"
