import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_owned_workspace
from app.db.models.workspace import Workspace
from app.db.queries import campaign as campaign_queries
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/workspaces/{workspace_id}/campaigns", tags=["campaigns"])


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


@router.get("/", response_model=PaginatedResponse[CampaignResponse])
def list_campaigns(
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[CampaignResponse]:
  items, total = campaign_queries.list_for_workspace(
    db, workspace.id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign(
  body: CampaignCreate,
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> CampaignResponse:
  return campaign_queries.create(
    db,
    workspace_id=workspace.id,
    title=body.title,
    objective=body.objective,
    target_audience=body.target_audience,
    region=body.region,
    platforms=body.platforms,
  )


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign=Depends(_get_campaign)) -> CampaignResponse:
  return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
  body: CampaignUpdate,
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> CampaignResponse:
  return campaign_queries.update(db, campaign, **body.model_dump(exclude_unset=True))


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> None:
  campaign_queries.delete(db, campaign)
