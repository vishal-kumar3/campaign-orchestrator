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


def delete(session: Session, document: Document) -> None:
  session.delete(document)
  session.commit()
