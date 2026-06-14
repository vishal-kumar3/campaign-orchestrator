import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.document import Document, DocumentChunk
from app.db.models.enums import DocumentStatus


@dataclass
class ChunkInput:
  chunk_index: int
  content: str
  embedding: list[float]
  metadata: dict | None = None


def delete_for_document(session: Session, document_id: uuid.UUID) -> None:
  session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
  session.commit()


def bulk_create(
  session: Session, document_id: uuid.UUID, chunks: list[ChunkInput]
) -> list[DocumentChunk]:
  rows = [
    DocumentChunk(
      document_id=document_id,
      chunk_index=chunk.chunk_index,
      content=chunk.content,
      embedding=chunk.embedding,
      metadata_=chunk.metadata,
    )
    for chunk in chunks
  ]
  session.add_all(rows)
  session.commit()
  for row in rows:
    session.refresh(row)
  return rows


def similarity_search(
  session: Session,
  *,
  knowledge_base_id: uuid.UUID,
  query_embedding: list[float],
  k: int,
) -> list[tuple[DocumentChunk, float]]:
  distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label(
    "distance"
  )
  rows = session.execute(
    select(DocumentChunk, distance_expr)
    .join(Document, DocumentChunk.document_id == Document.id)
    .where(
      Document.knowledge_base_id == knowledge_base_id,
      Document.status == DocumentStatus.INDEXED,
      DocumentChunk.embedding.is_not(None),
    )
    .order_by(distance_expr)
    .limit(k)
  ).all()
  return [(chunk, float(distance)) for chunk, distance in rows]
