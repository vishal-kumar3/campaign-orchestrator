import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_owned_workspace
from app.db.models.document import Document
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.workspace import Workspace
from app.db.queries import document as document_queries
from app.db.queries import knowledge_base as knowledge_base_queries
from app.schemas.common import PaginatedResponse
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter(
  prefix="/workspaces/{workspace_id}/knowledge-bases/{knowledge_base_id}/documents",
  tags=["documents"],
)


def _get_knowledge_base(
  workspace_id: uuid.UUID,
  knowledge_base_id: uuid.UUID,
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> KnowledgeBase:
  if workspace.id != workspace_id:
    raise HTTPException(status_code=404, detail="Knowledge base not found")
  knowledge_base = knowledge_base_queries.get_by_id_for_workspace(
    db, knowledge_base_id, workspace.id
  )
  if knowledge_base is None:
    raise HTTPException(status_code=404, detail="Knowledge base not found")
  return knowledge_base


def _get_document(
  workspace_id: uuid.UUID,
  knowledge_base_id: uuid.UUID,
  document_id: uuid.UUID,
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
  db: Session = Depends(get_db),
) -> Document:
  document = document_queries.get_by_id_for_knowledge_base(
    db, document_id, knowledge_base.id
  )
  if document is None:
    raise HTTPException(status_code=404, detail="Document not found")
  return document


@router.get("/", response_model=PaginatedResponse[DocumentResponse])
def list_documents(
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
  db: Session = Depends(get_db),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[DocumentResponse]:
  items, total = document_queries.list_for_knowledge_base(
    db, knowledge_base.id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.post("/", response_model=DocumentResponse, status_code=201)
def create_document(
  body: DocumentCreate,
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
  db: Session = Depends(get_db),
) -> DocumentResponse:
  return document_queries.create(
    db,
    knowledge_base_id=knowledge_base.id,
    file_name=body.file_name,
    file_url=body.file_url,
    mime_type=body.mime_type,
  )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document: Document = Depends(_get_document)) -> DocumentResponse:
  return document


@router.delete("/{document_id}", status_code=204)
def delete_document(
  document: Document = Depends(_get_document),
  db: Session = Depends(get_db),
) -> None:
  document_queries.delete(db, document)
