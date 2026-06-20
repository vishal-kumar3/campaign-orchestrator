import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_owned_workspace
from app.core.config import settings
from app.db.models.document import Document
from app.db.models.enums import DocumentStatus
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.workspace import Workspace
from app.db.queries import document as document_queries
from app.db.queries import document_chunk as document_chunk_queries
from app.db.queries import knowledge_base as knowledge_base_queries
from app.db.session import SessionLocal
from app.schemas.common import PaginatedResponse
from app.schemas.document import (
  DocumentCreate,
  DocumentProcessResponse,
  DocumentResponse,
  DocumentUploadResponse,
)
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

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


def _run_ingestion(document_id: uuid.UUID) -> None:
  from app.tasks.ingestion import ingest_document_task

  ingest_document_task.delay(str(document_id))


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


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
  file: UploadFile = File(...),
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> DocumentUploadResponse:
  if file.content_type not in ("application/pdf", "application/x-pdf"):
    raise HTTPException(status_code=422, detail="Only PDF files are supported")

  data = await file.read()
  if len(data) > settings.max_upload_bytes:
    raise HTTPException(status_code=413, detail="File too large")
  if not data:
    raise HTTPException(status_code=422, detail="Empty file")

  document_id = uuid.uuid4()
  storage = get_storage()
  file_name = file.filename or "document.pdf"
  key = storage.build_key(workspace.id, knowledge_base.id, document_id, file_name)
  storage.save(key, data)

  document = document_queries.create_pending(
    db,
    document_id=document_id,
    knowledge_base_id=knowledge_base.id,
    file_name=file_name,
    file_url=key,
    mime_type=file.content_type,
  )
  return DocumentUploadResponse(
    document_id=document.id,
    file_name=document.file_name,
    file_url=document.file_url,
    mime_type=document.mime_type,
    status=document.status,
  )


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


@router.post("/{document_id}/process", response_model=DocumentProcessResponse, status_code=202)
def process_document(
  background_tasks: BackgroundTasks,
  document: Document = Depends(_get_document),
  db: Session = Depends(get_db),
) -> DocumentProcessResponse:
  if document.status == DocumentStatus.PROCESSING:
    raise HTTPException(status_code=409, detail="Document is already processing")

  if document.status == DocumentStatus.INDEXED:
    document_chunk_queries.delete_for_document(db, document.id)

  document_queries.update_status(db, document, status=DocumentStatus.PROCESSING)
  background_tasks.add_task(_run_ingestion, document.id)
  return DocumentProcessResponse(document_id=document.id, status=DocumentStatus.PROCESSING)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document: Document = Depends(_get_document)) -> DocumentResponse:
  return document


@router.delete("/{document_id}", status_code=204)
def delete_document(
  document: Document = Depends(_get_document),
  db: Session = Depends(get_db),
) -> None:
  storage = get_storage()
  try:
    storage.delete(document.file_url)
  except (ValueError, FileNotFoundError, OSError):
    logger.warning("Failed to delete file for document %s", document.id)
  document_queries.delete(db, document)
