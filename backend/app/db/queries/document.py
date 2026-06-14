import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.enums import DocumentStatus


def get_by_id_for_knowledge_base(
  session: Session, document_id: uuid.UUID, knowledge_base_id: uuid.UUID
) -> Document | None:
  return session.scalar(
    select(Document).where(
      Document.id == document_id,
      Document.knowledge_base_id == knowledge_base_id,
    )
  )


def get_by_id(session: Session, document_id: uuid.UUID) -> Document | None:
  return session.get(Document, document_id)


def list_for_knowledge_base(
  session: Session, knowledge_base_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[Document], int]:
  base = select(Document).where(Document.knowledge_base_id == knowledge_base_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total


def create(
  session: Session,
  *,
  knowledge_base_id: uuid.UUID,
  file_name: str,
  file_url: str,
  mime_type: str | None,
) -> Document:
  document = Document(
    knowledge_base_id=knowledge_base_id,
    file_name=file_name,
    file_url=file_url,
    mime_type=mime_type,
    status=DocumentStatus.PENDING,
  )
  session.add(document)
  session.commit()
  session.refresh(document)
  return document


def create_pending(
  session: Session,
  *,
  document_id: uuid.UUID,
  knowledge_base_id: uuid.UUID,
  file_name: str,
  file_url: str,
  mime_type: str | None,
) -> Document:
  document = Document(
    id=document_id,
    knowledge_base_id=knowledge_base_id,
    file_name=file_name,
    file_url=file_url,
    mime_type=mime_type,
    status=DocumentStatus.PENDING,
  )
  session.add(document)
  session.commit()
  session.refresh(document)
  return document


def update_status(
  session: Session,
  document: Document,
  *,
  status: DocumentStatus,
  processing_error: str | None = None,
) -> Document:
  document.status = status
  if processing_error is not None:
    document.processing_error = processing_error
  elif status != DocumentStatus.FAILED:
    document.processing_error = None
  session.commit()
  session.refresh(document)
  return document


def count_indexed_for_knowledge_base(
  session: Session, knowledge_base_id: uuid.UUID
) -> int:
  return (
    session.scalar(
      select(func.count())
      .select_from(Document)
      .where(
        Document.knowledge_base_id == knowledge_base_id,
        Document.status == DocumentStatus.INDEXED,
      )
    )
    or 0
  )


def delete(session: Session, document: Document) -> None:
  session.delete(document)
  session.commit()
