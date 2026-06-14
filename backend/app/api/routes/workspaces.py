import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db, get_owned_workspace
from app.db.models.workspace import Workspace
from app.db.queries import workspace as workspace_queries
from app.schemas.common import PaginatedResponse
from app.schemas.workspace import (
  WorkspaceCreate,
  WorkspaceResponse,
  WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=PaginatedResponse[WorkspaceResponse])
def list_workspaces(
  db: Session = Depends(get_db),
  user_id: str = Depends(get_current_user_id),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[WorkspaceResponse]:
  items, total = workspace_queries.list_for_owner(
    db, user_id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.post("/", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
  body: WorkspaceCreate,
  db: Session = Depends(get_db),
  user_id: str = Depends(get_current_user_id),
) -> WorkspaceResponse:
  return workspace_queries.create(
    db, owner_id=user_id, name=body.name, description=body.description
  )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
  workspace: Workspace = Depends(get_owned_workspace),
) -> WorkspaceResponse:
  return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
  body: WorkspaceUpdate,
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> WorkspaceResponse:
  data = body.model_dump(exclude_unset=True)
  return workspace_queries.update(db, workspace, **data)


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> None:
  workspace_queries.delete(db, workspace)
