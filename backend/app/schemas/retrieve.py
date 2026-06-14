import uuid

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
  chunk_id: uuid.UUID
  document_id: uuid.UUID
  chunk_index: int
  content: str
  score: float
  metadata: dict | None


class RetrieveResponse(BaseModel):
  query: str
  knowledge_base_id: uuid.UUID
  chunks: list[RetrievedChunk]
