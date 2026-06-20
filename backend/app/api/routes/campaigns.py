import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from agent.graph import is_checkpointer_enabled
from app.api.deps import get_db, get_owned_workspace
from app.db.models.campaign import Campaign
from app.db.models.enums import CampaignStatus, ContentStatus
from app.db.models.workspace import Workspace
from app.db.queries import agent_log as agent_log_queries
from app.db.queries import agent_run as agent_run_queries
from app.db.queries import campaign as campaign_queries
from app.db.queries import content as content_queries
from app.db.queries import knowledge_base as knowledge_base_queries
from app.db.queries import research_snapshot as research_snapshot_queries
from app.db.queries import workflow_thread as workflow_thread_queries
from app.db.session import SessionLocal
from app.schemas.analytics import CampaignAnalyticsResponse
from app.schemas.agent import AgentLogResponse, AgentRunResponse
from app.schemas.approve import ApproveCampaignRequest, ApproveCampaignResponse
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate
from app.schemas.common import PaginatedResponse
from app.schemas.execute import ExecuteCampaignResponse
from app.schemas.research import ResearchSnapshotResponse
from app.services.campaign_executor import (
  execute_campaign_background,
  prepare_execution,
  resolve_approval_thread,
  resume_campaign_background,
  validate_campaign_approvable,
)
from app.services.campaign_stream import campaign_event_stream
from app.services.analytics import build_campaign_analytics

logger = logging.getLogger(__name__)

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


def _validate_knowledge_base_in_workspace(
  db: Session, workspace_id: uuid.UUID, knowledge_base_id: uuid.UUID | None
) -> None:
  if knowledge_base_id is None:
    return
  kb = knowledge_base_queries.get_by_id_for_workspace(db, knowledge_base_id, workspace_id)
  if kb is None:
    raise HTTPException(status_code=422, detail="knowledge_base_id not found in workspace")


def _serialize_campaign_body(body: CampaignCreate | CampaignUpdate) -> dict:
  data = body.model_dump(exclude_unset=True)
  if "competitor_urls" in data and data["competitor_urls"] is not None:
    data["competitor_urls"] = [str(url) for url in data["competitor_urls"]]
  return data


def _run_campaign_background(
  campaign_id: uuid.UUID, workspace_id: uuid.UUID, thread_id: str
) -> None:
  asyncio.run(
    execute_campaign_background(SessionLocal, campaign_id, workspace_id, thread_id)
  )


def _resume_campaign_background(
  campaign_id: uuid.UUID, workspace_id: uuid.UUID, thread_id: str
) -> None:
  asyncio.run(
    resume_campaign_background(SessionLocal, campaign_id, workspace_id, thread_id)
  )


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
  _validate_knowledge_base_in_workspace(db, workspace.id, body.knowledge_base_id)
  return campaign_queries.create(
    db,
    workspace_id=workspace.id,
    title=body.title,
    objective=body.objective,
    target_audience=body.target_audience,
    region=body.region,
    platforms=body.platforms,
    knowledge_base_id=body.knowledge_base_id,
    competitor_urls=[str(url) for url in body.competitor_urls]
    if body.competitor_urls
    else None,
  )


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign=Depends(_get_campaign)) -> CampaignResponse:
  return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
  body: CampaignUpdate,
  campaign: Campaign = Depends(_get_campaign),
  workspace: Workspace = Depends(get_owned_workspace),
  db: Session = Depends(get_db),
) -> CampaignResponse:
  data = _serialize_campaign_body(body)
  if "knowledge_base_id" in data:
    _validate_knowledge_base_in_workspace(db, workspace.id, data["knowledge_base_id"])
  return campaign_queries.update(db, campaign, **data)


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> None:
  campaign_queries.delete(db, campaign)


@router.post("/{campaign_id}/execute", response_model=ExecuteCampaignResponse, status_code=202)
def execute_campaign(
  background_tasks: BackgroundTasks,
  campaign: Campaign = Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> ExecuteCampaignResponse:
  thread_id = str(uuid.uuid4())
  try:
    prepare_execution(db, campaign, thread_id=thread_id)
  except ValueError as exc:
    raise HTTPException(status_code=409, detail=str(exc)) from exc

  background_tasks.add_task(
    _run_campaign_background,
    campaign.id,
    campaign.workspace_id,
    thread_id,
  )

  db.refresh(campaign)
  return ExecuteCampaignResponse(
    campaign_id=campaign.id,
    status=campaign.status,
    thread_id=thread_id,
  )


@router.get(
  "/{campaign_id}/research-snapshots",
  response_model=PaginatedResponse[ResearchSnapshotResponse],
)
def list_research_snapshots(
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[ResearchSnapshotResponse]:
  items, total = research_snapshot_queries.list_for_campaign(
    db, campaign.id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.get("/{campaign_id}/agent-runs", response_model=PaginatedResponse[AgentRunResponse])
def list_agent_runs(
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
  limit: int = Query(default=50, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[AgentRunResponse]:
  items, total = agent_run_queries.list_for_campaign(
    db, campaign.id, limit=limit, offset=offset
  )
  return PaginatedResponse(items=items, total=total)


@router.get(
  "/{campaign_id}/agent-runs/{run_id}/logs",
  response_model=PaginatedResponse[AgentLogResponse],
)
def list_agent_logs(
  run_id: uuid.UUID,
  campaign=Depends(_get_campaign),
  db: Session = Depends(get_db),
  limit: int = Query(default=100, ge=1, le=500),
  offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[AgentLogResponse]:
  run = agent_run_queries.get_by_id_for_campaign(db, run_id, campaign.id)
  if run is None:
    raise HTTPException(status_code=404, detail="Agent run not found")
  items, total = agent_log_queries.list_for_run(db, run_id, limit=limit, offset=offset)
  return PaginatedResponse(items=items, total=total)


@router.get("/{campaign_id}/stream")
async def stream_campaign_events(
  campaign: Campaign = Depends(_get_campaign),
) -> StreamingResponse:
  return StreamingResponse(
    campaign_event_stream(SessionLocal, campaign.id),
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  )


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalyticsResponse)
def get_campaign_analytics(
  campaign: Campaign = Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> CampaignAnalyticsResponse:
  return build_campaign_analytics(db, campaign.id)


@router.post(
  "/{campaign_id}/approve",
  response_model=ApproveCampaignResponse,
)
def approve_campaign(
  body: ApproveCampaignRequest,
  background_tasks: BackgroundTasks,
  response: Response,
  campaign: Campaign = Depends(_get_campaign),
  db: Session = Depends(get_db),
) -> ApproveCampaignResponse:
  validate_campaign_approvable(db, campaign)

  if not is_checkpointer_enabled():
    raise HTTPException(
      status_code=503,
      detail="Campaign resume is unavailable: LangGraph checkpointer not enabled",
    )

  approved_count = sum(1 for item in body.contents if item.status == "approved")
  rejected_count = sum(1 for item in body.contents if item.status == "rejected")

  try:
    content_queries.bulk_update_approval(
      db,
      campaign.id,
      items=[
        (
          item.id,
          item.content,
          ContentStatus.APPROVED if item.status == "approved" else ContentStatus.REJECTED,
          item.scheduled_at,
        )
        for item in body.contents
      ],
    )
  except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc)) from exc

  if rejected_count == len(body.contents):
    if body.reject_all_to_draft:
      campaign_queries.transition_status(
        db,
        campaign,
        to=CampaignStatus.DRAFT,
        allowed_from={CampaignStatus.APPROVAL_PENDING},
      )
      thread = workflow_thread_queries.get_latest_for_campaign(db, campaign.id)
      if thread:
        workflow_thread_queries.update_status(db, thread, status="completed")
      db.refresh(campaign)
      return ApproveCampaignResponse(
        campaign_id=campaign.id,
        status=campaign.status,
        approved_count=0,
        rejected_count=rejected_count,
        resuming=False,
      )

    db.refresh(campaign)
    return ApproveCampaignResponse(
      campaign_id=campaign.id,
      status=campaign.status,
      approved_count=0,
      rejected_count=rejected_count,
      resuming=False,
    )

  if approved_count == 0:
    db.refresh(campaign)
    return ApproveCampaignResponse(
      campaign_id=campaign.id,
      status=campaign.status,
      approved_count=0,
      rejected_count=rejected_count,
      resuming=False,
    )

  thread_id = resolve_approval_thread(db, campaign.id)
  background_tasks.add_task(
    _resume_campaign_background,
    campaign.id,
    campaign.workspace_id,
    thread_id,
  )

  db.refresh(campaign)
  response.status_code = 202
  return ApproveCampaignResponse(
    campaign_id=campaign.id,
    status=campaign.status,
    approved_count=approved_count,
    rejected_count=rejected_count,
    resuming=True,
  )
