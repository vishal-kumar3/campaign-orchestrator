import io
import logging
import uuid
from dataclasses import dataclass

import tiktoken
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document
from app.db.models.enums import DocumentStatus
from app.db.queries import document as document_queries
from app.db.queries import document_chunk as document_chunk_queries
from app.db.queries.document_chunk import ChunkInput
from app.services import embeddings
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

_ENCODING = tiktoken.get_encoding("cl100k_base")
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class BrandContextChunk:
  chunk_id: uuid.UUID
  document_id: uuid.UUID
  chunk_index: int
  content: str
  score: float
  metadata: dict | None


def retrieve_brand_context(
  session: Session,
  *,
  knowledge_base_id: uuid.UUID,
  query: str,
  k: int | None = None,
) -> list[BrandContextChunk]:
  limit = k or settings.retrieve_default_k
  query_embedding = embeddings.embed_query(query)
  results = document_chunk_queries.similarity_search(
    session,
    knowledge_base_id=knowledge_base_id,
    query_embedding=query_embedding,
    k=limit,
  )
  return [
    BrandContextChunk(
      chunk_id=chunk.id,
      document_id=chunk.document_id,
      chunk_index=chunk.chunk_index,
      content=chunk.content,
      score=max(0.0, 1.0 - distance),
      metadata=chunk.metadata_,
    )
    for chunk, distance in results
  ]


def extract_pdf_text(pdf_bytes: bytes) -> str:
  reader = PdfReader(io.BytesIO(pdf_bytes))
  pages = [page.extract_text() or "" for page in reader.pages]
  return "\n".join(pages).strip()


def _count_tokens(text: str) -> int:
  return len(_ENCODING.encode(text))


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
  if not text:
    return []

  chunks: list[str] = []
  start = 0
  text_len = len(text)

  while start < text_len:
    end = min(text_len, start + chunk_size * 4)
    piece = text[start:end]

    if _count_tokens(piece) <= chunk_size:
      if piece.strip():
        chunks.append(piece.strip())
      if end >= text_len:
        break
      start = max(start + 1, end - overlap * 4)
      continue

    split_at = None
    for separator in _SEPARATORS:
      idx = piece.rfind(separator)
      if idx > chunk_size:
        split_at = idx + len(separator)
        break

    if split_at is None:
      split_at = len(piece)

    segment = piece[:split_at].strip()
    if segment:
      chunks.append(segment)

    if split_at == 0:
      start += 1
    else:
      start = start + split_at - overlap * 4

  return chunks


def ingest_document(session: Session, document: Document) -> None:
  storage = get_storage()
  try:
    pdf_bytes = storage.read(document.file_url)
    text = extract_pdf_text(pdf_bytes)
    if not text:
      raise ValueError("No extractable text in PDF")

    chunks = chunk_text(
      text,
      chunk_size=settings.chunk_size_tokens,
      overlap=settings.chunk_overlap_tokens,
    )
    if not chunks:
      raise ValueError("No extractable text in PDF")

    vectors = embeddings.embed_texts(chunks)
    document_chunk_queries.delete_for_document(session, document.id)

    chunk_rows = [
      ChunkInput(
        chunk_index=index,
        content=content,
        embedding=vector,
        metadata={
          "token_count": _count_tokens(content),
          "source_file": document.file_name,
        },
      )
      for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True))
    ]
    document_chunk_queries.bulk_create(session, document.id, chunk_rows)
    document_queries.update_status(session, document, status=DocumentStatus.INDEXED)
  except Exception as exc:
    logger.exception("Document ingestion failed for %s", document.id)
    document_queries.update_status(
      session,
      document,
      status=DocumentStatus.FAILED,
      processing_error=str(exc)[:500],
    )
