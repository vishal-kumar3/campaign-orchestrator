import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_owned_workspace
from app.db.models.content import CampaignContent
from app.db.models.workspace import Workspace
from app.db.queries import campaign as campaign_queries
from app.db.queries import content as content_queries
from app.schemas.common import PaginatedResponse
from app.schemas.content import ContentCreate, ContentResponse, ContentUpdate

router = APIRouter(
  prefix="/workspaces/{workspace_id}/campaigns/{campaign_id}/contents",
  tags=["contents"],
)


def _get_campaign(
  workspace_id: uuid.UUID,
  campaign_id: uuid.UUID,
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
):
  if workspace.id != workspace_id:
    raise HTTPException(status_code=404, detail="Campaign not found")
  campaign = campaign_queries.get_by_id_for_workspace(db, campaign_id, workspace.id)
  if campaign is None:
    raise HTTPException(status_code=404, detail="Campaign not found")
  return campaign


def _get_content(
  workspace_id: uuid.UUID,
  campaign_id: uuid.UUID,
  content_id: uuid.UUID,
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> CampaignContent:
  content = content_queries.get_by_id_for_campaign(db, content_id, campaign.id)
  if content is None:
    raise HTTPException(status_code=404, detail="Content not found")
  return content


@router.get("/", response_model=PaginatedResponse[ContentResponse])
def list_contents(
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[ContentResponse]:
  items, total = content_queries.list_for_campaign(
    db, campaign.id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.post("/", response_model=ContentResponse, status_code=201)
def create_content(
  body: ContentCreate,
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> ContentResponse:
  return content_queries.create(
    db,
    campaign_id=campaign.id,
    platform=body.platform,
    title=body.title,
    content=body.content,
    status=body.status,
  )


@router.get("/{content_id}", response_model=ContentResponse)
def get_content(content: CampaignContent = Depends(_get_content)) -> ContentResponse:
  return content


@router.patch("/{content_id}", response_model=ContentResponse)
def update_content(
  body: ContentUpdate,
  content: CampaignContent = Depends(_get_content),
  db: Session = Depends(get_db),
) -> ContentResponse:
  return content_queries.update(db, content, **body.model_dump(exclude_unset=True))


@router.delete("/{content_id}", status_code=204)
def delete_content(
  content: CampaignContent = Depends(_get_content),
  db: Session = Depends(get_db),
) -> None:
  content_queries.delete(db, content)
