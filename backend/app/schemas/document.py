import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import DocumentStatus


class DocumentCreate(BaseModel):
  file_name: str = Field(min_length=1)
  file_url: str = Field(min_length=1)
  mime_type: str | None = None


class DocumentUploadResponse(BaseModel):
  document_id: uuid.UUID
  file_name: str
  file_url: str
  mime_type: str | None
  status: DocumentStatus


class DocumentProcessResponse(BaseModel):
  document_id: uuid.UUID
  status: DocumentStatus
  message: str = "Processing started"


class DocumentResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  knowledge_base_id: uuid.UUID
  file_name: str
  file_url: str
  mime_type: str | None
  status: DocumentStatus
  processing_error: str | None = None
  created_at: datetime
