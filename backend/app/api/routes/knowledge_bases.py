import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_owned_workspace
from app.db.models.enums import KnowledgeScope
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.workspace import Workspace
from app.db.queries import campaign as campaign_queries
from app.db.queries import knowledge_base as knowledge_base_queries
from app.schemas.common import PaginatedResponse
from app.schemas.knowledge_base import (
  KnowledgeBaseCreate,
  KnowledgeBaseResponse,
  KnowledgeBaseUpdate,
)

router = APIRouter(
  prefix="/workspaces/{workspace_id}/knowledge-bases", tags=["knowledge-bases"]
)


def _validate_campaign_in_workspace(
  db: Session, workspace_id: uuid.UUID, campaign_id: uuid.UUID | None
) -> None:
  if campaign_id is None:
    return
  campaign = campaign_queries.get_by_id_for_workspace(db, campaign_id, workspace_id)
  if campaign is None:
    raise HTTPException(status_code=422, detail="campaign_id not found in workspace")


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


@router.get("/", response_model=PaginatedResponse[KnowledgeBaseResponse])
def list_knowledge_bases(
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[KnowledgeBaseResponse]:
  items, total = knowledge_base_queries.list_for_workspace(
    db, workspace.id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
def create_knowledge_base(
  body: KnowledgeBaseCreate,
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> KnowledgeBaseResponse:
  if body.scope == KnowledgeScope.CAMPAIGN:
    _validate_campaign_in_workspace(db, workspace.id, body.campaign_id)
  return knowledge_base_queries.create(
    db,
    workspace_id=workspace.id,
    name=body.name,
    scope=body.scope,
    campaign_id=body.campaign_id,
  )


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
) -> KnowledgeBaseResponse:
  return knowledge_base


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
  body: KnowledgeBaseUpdate,
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> KnowledgeBaseResponse:
  data = body.model_dump(exclude_unset=True)
  scope = data.get("scope", knowledge_base.scope)
  campaign_id = data.get("campaign_id", knowledge_base.campaign_id)

  if scope == KnowledgeScope.WORKSPACE:
    campaign_id = None
  elif scope == KnowledgeScope.CAMPAIGN:
    if campaign_id is None:
      raise HTTPException(
        status_code=422, detail="campaign_id is required when scope is campaign"
      )
    _validate_campaign_in_workspace(db, workspace.id, campaign_id)

  if "scope" in data:
    data["scope"] = scope
  if "scope" in data or "campaign_id" in data:
    data["campaign_id"] = campaign_id

  return knowledge_base_queries.update(db, knowledge_base, **data)


@router.delete("/{knowledge_base_id}", status_code=204)
def delete_knowledge_base(
  knowledge_base: KnowledgeBase = Depends(_get_knowledge_base),
  db: Session = Depends(get_db),
) -> None:
  knowledge_base_queries.delete(db, knowledge_base)
