import logging
import uuid
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session, sessionmaker

from agent.graph import is_checkpointer_enabled
from agent.run import resume_campaign_graph, run_campaign_graph
from agent.state import AgentCallbacks, AgentSettings, CampaignGraphState, GraphConfigurable
from app.core.config import settings
from app.db.models.campaign import Campaign
from app.db.models.enums import CampaignStatus, ContentPlatform, ContentStatus, LogLevel
from app.db.queries import agent_log as agent_log_queries
from app.db.queries import agent_run as agent_run_queries
from app.db.queries import campaign as campaign_queries
from app.db.queries import content as content_queries
from app.db.queries import document as document_queries
from app.db.queries import knowledge_base as knowledge_base_queries
from app.db.queries import research_snapshot as research_snapshot_queries
from app.db.queries import workflow_thread as workflow_thread_queries
from app.services.event_bus import publish_campaign_event
from app.services.publisher import publish_twitter_post
from app.services.rag import retrieve_brand_context

logger = logging.getLogger(__name__)

_SUPPORTED_PLATFORMS = {ContentPlatform.TWITTER, ContentPlatform.LINKEDIN}

_STATUS_MAP = {
  "draft": CampaignStatus.DRAFT,
  "researching": CampaignStatus.RESEARCHING,
  "generating": CampaignStatus.GENERATING,
  "approval_pending": CampaignStatus.APPROVAL_PENDING,
  "completed": CampaignStatus.COMPLETED,
  "failed": CampaignStatus.FAILED,
}


@dataclass
class ExecuteContext:
  campaign_id: uuid.UUID
  workspace_id: uuid.UUID
  thread_id: str


def validate_campaign_executable(session: Session, campaign: Campaign) -> None:
  if campaign.status != CampaignStatus.DRAFT:
    raise HTTPException(
      status_code=409,
      detail=f"Campaign must be in draft status to execute (current: {campaign.status.value})",
    )
  if campaign.knowledge_base_id is None:
    raise HTTPException(
      status_code=422,
      detail="Campaign must have a linked knowledge base before execution",
    )

  kb = knowledge_base_queries.get_by_id_for_workspace(
    session, campaign.knowledge_base_id, campaign.workspace_id
  )
  if kb is None:
    raise HTTPException(status_code=422, detail="Linked knowledge base not found in workspace")

  indexed_count = document_queries.count_indexed_for_knowledge_base(
    session, campaign.knowledge_base_id
  )
  if indexed_count == 0:
    raise HTTPException(
      status_code=422,
      detail="Knowledge base must have at least one indexed document",
    )

  platforms = campaign.platforms or []
  if not any(p in _SUPPORTED_PLATFORMS for p in platforms):
    raise HTTPException(
      status_code=422,
      detail="Campaign must include at least one of: twitter, linkedin",
    )


def prepare_execution(
  session: Session, campaign: Campaign, *, thread_id: str
) -> ExecuteContext:
  validate_campaign_executable(session, campaign)
  campaign_queries.transition_status(
    session,
    campaign,
    to=CampaignStatus.RESEARCHING,
    allowed_from={CampaignStatus.DRAFT},
  )
  publish_campaign_event(
    campaign.id,
    {"type": "status", "status": CampaignStatus.RESEARCHING.value},
  )
  workflow_thread_queries.create(
    session,
    campaign_id=campaign.id,
    thread_id=thread_id,
    status="running",
  )
  return ExecuteContext(
    campaign_id=campaign.id,
    workspace_id=campaign.workspace_id,
    thread_id=thread_id,
  )


def _build_platforms(campaign: Campaign) -> list[str]:
  platforms = campaign.platforms or []
  return [
    p.value
    for p in platforms
    if p in _SUPPORTED_PLATFORMS
  ]


def _publish_log_event(
  campaign_id: uuid.UUID,
  *,
  run_id: str,
  node_name: str,
  level: str,
  message: str,
  created_at: str,
  log_id: str | None = None,
) -> None:
  publish_campaign_event(
    campaign_id,
    {
      "type": "log",
      "id": log_id,
      "run_id": run_id,
      "node_name": node_name,
      "level": level,
      "message": message,
      "created_at": created_at,
    },
  )


def _publish_status_event(campaign_id: uuid.UUID, status: str) -> None:
  publish_campaign_event(
    campaign_id,
    {"type": "status", "status": status},
  )


def _build_callbacks(
  session_factory: sessionmaker,
  ctx: ExecuteContext,
) -> AgentCallbacks:
  campaign_id = ctx.campaign_id

  def _with_session(fn):
    def wrapper(*args, **kwargs):
      db = session_factory()
      try:
        return fn(db, *args, **kwargs)
      finally:
        db.close()

    return wrapper

  @_with_session
  def create_agent_run(db: Session, agent_name: str, input_data: dict | None) -> str:
    run = agent_run_queries.create(
      db, campaign_id=campaign_id, agent_name=agent_name, input_data=input_data
    )
    return str(run.id)

  @_with_session
  def complete_agent_run(db: Session, run_id: str, output: dict | None) -> None:
    run = agent_run_queries.get_by_id_for_campaign(db, uuid.UUID(run_id), campaign_id)
    if run:
      agent_run_queries.complete(db, run, output=output)

  @_with_session
  def fail_agent_run(db: Session, run_id: str, output: dict | None) -> None:
    run = agent_run_queries.get_by_id_for_campaign(db, uuid.UUID(run_id), campaign_id)
    if run:
      agent_run_queries.fail(db, run, output=output)

  @_with_session
  def log(
    db: Session,
    run_id: str,
    node_name: str,
    message: str,
    level: str = "info",
  ) -> None:
    log_level = LogLevel.INFO
    if level in {item.value for item in LogLevel}:
      log_level = LogLevel(level)
    row = agent_log_queries.create(
      db,
      run_id=uuid.UUID(run_id),
      node_name=node_name,
      message=message,
      level=log_level,
    )
    _publish_log_event(
      campaign_id,
      run_id=run_id,
      node_name=node_name,
      level=level,
      message=message,
      created_at=row.created_at.isoformat(),
      log_id=str(row.id),
    )

  @_with_session
  def create_research_snapshot(
    db: Session, summary: str, raw_data: dict | None
  ) -> str:
    snapshot = research_snapshot_queries.create(
      db,
      campaign_id=campaign_id,
      summary=summary,
      raw_data=raw_data,
    )
    return str(snapshot.id)

  @_with_session
  def get_research_summary(db: Session, snapshot_id: str) -> str:
    snapshot = research_snapshot_queries.get_by_id(db, uuid.UUID(snapshot_id))
    if snapshot is None or not snapshot.summary:
      raise ValueError(f"Research snapshot {snapshot_id} not found")
    return snapshot.summary

  @_with_session
  def create_content(
    db: Session, platform: str, title: str | None, content: str
  ) -> str:
    piece = content_queries.create(
      db,
      campaign_id=campaign_id,
      platform=ContentPlatform(platform),
      title=title,
      content=content,
      status=None,
    )
    return str(piece.id)

  @_with_session
  def retrieve_context(db: Session, kb_id: str, query: str, k: int) -> list[dict]:
    chunks = retrieve_brand_context(
      db,
      knowledge_base_id=uuid.UUID(kb_id),
      query=query,
      k=k,
    )
    return [
      {
        "chunk_id": str(c.chunk_id),
        "content": c.content,
        "score": c.score,
        "metadata": c.metadata,
      }
      for c in chunks
    ]

  @_with_session
  def transition_campaign_status(db: Session, from_status: str, to_status: str) -> None:
    campaign = campaign_queries.get_by_id_for_workspace(
      db, campaign_id, ctx.workspace_id
    )
    if campaign is None:
      raise ValueError("Campaign not found during status transition")
    from_enum = _STATUS_MAP[from_status]
    to_enum = _STATUS_MAP[to_status]
    campaign_queries.transition_status(
      db,
      campaign,
      to=to_enum,
      allowed_from={from_enum},
    )
    _publish_status_event(campaign_id, to_status)

  @_with_session
  def get_approved_contents(db: Session) -> list[dict]:
    items = content_queries.get_approved_for_campaign(db, campaign_id)
    return [
      {
        "id": str(item.id),
        "platform": item.platform.value,
        "content": item.content,
      }
      for item in items
    ]

  @_with_session
  def mark_content_published(db: Session, content_id: str, external_post_id: str) -> None:
    content = content_queries.get_by_id_for_campaign(
      db, uuid.UUID(content_id), campaign_id
    )
    if content is None:
      raise ValueError(f"Content {content_id} not found")
    content_queries.mark_published(db, content, external_post_id=external_post_id)

  @_with_session
  def mark_content_failed(db: Session, content_id: str, _error: str) -> None:
    content = content_queries.get_by_id_for_campaign(
      db, uuid.UUID(content_id), campaign_id
    )
    if content is None:
      raise ValueError(f"Content {content_id} not found")
    content_queries.mark_failed(db, content)

  def publish_twitter(text: str) -> str:
    return publish_twitter_post(text)

  return AgentCallbacks(
    create_agent_run=lambda name, data: create_agent_run(name, data),
    complete_agent_run=lambda run_id, output: complete_agent_run(run_id, output),
    fail_agent_run=lambda run_id, output: fail_agent_run(run_id, output),
    log=lambda run_id, node, message, level="info": log(
      run_id, node, message, level
    ),
    create_research_snapshot=lambda summary, raw: create_research_snapshot(
      summary, raw
    ),
    get_research_summary=lambda snapshot_id: get_research_summary(snapshot_id),
    create_content=lambda platform, title, content: create_content(
      platform, title, content
    ),
    retrieve_brand_context=lambda kb_id, query, k: retrieve_context(
      kb_id, query, k
    ),
    transition_campaign_status=lambda from_s, to_s: transition_campaign_status(
      from_s, to_s
    ),
    get_approved_contents=lambda: get_approved_contents(),
    mark_content_published=lambda cid, post_id: mark_content_published(cid, post_id),
    mark_content_failed=lambda cid, err: mark_content_failed(cid, err),
    publish_twitter=publish_twitter,
  )


def _build_initial_state(campaign: Campaign, thread_id: str) -> CampaignGraphState:
  return CampaignGraphState(
    campaign_id=str(campaign.id),
    workspace_id=str(campaign.workspace_id),
    thread_id=thread_id,
    objective=campaign.objective,
    target_audience=campaign.target_audience,
    platforms=_build_platforms(campaign),
    knowledge_base_id=str(campaign.knowledge_base_id),
    competitor_urls=list(campaign.competitor_urls or []),
    research_snapshot_id=None,
    content_ids=[],
    error=None,
  )


def _build_graph_config(
  session_factory: sessionmaker,
  ctx: ExecuteContext,
) -> GraphConfigurable:
  callbacks = _build_callbacks(session_factory, ctx)
  return {
    "callbacks": callbacks,
    "settings": AgentSettings(
      google_api_key=settings.google_api_key,
      chat_model=settings.chat_model,
      tavily_api_key=settings.tavily_api_key,
      retrieve_default_k=settings.retrieve_default_k,
    ),
  }


def _finalize_thread_status(
  session_factory: sessionmaker,
  thread_id: str,
  campaign_id: uuid.UUID,
  workspace_id: uuid.UUID,
) -> None:
  db = session_factory()
  try:
    campaign = campaign_queries.get_by_id_for_workspace(db, campaign_id, workspace_id)
    wf = workflow_thread_queries.get_latest_for_campaign(db, campaign_id)
    if wf is None or wf.thread_id != thread_id:
      return

    if campaign and campaign.status == CampaignStatus.APPROVAL_PENDING:
      workflow_thread_queries.update_status(db, wf, status="awaiting_approval")
    elif campaign and campaign.status == CampaignStatus.COMPLETED:
      workflow_thread_queries.update_status(db, wf, status="completed")
    elif campaign and campaign.status == CampaignStatus.FAILED:
      workflow_thread_queries.update_status(db, wf, status="failed")
    else:
      workflow_thread_queries.update_status(db, wf, status="completed")
  finally:
    db.close()


async def execute_campaign_background(
  session_factory: sessionmaker,
  campaign_id: uuid.UUID,
  workspace_id: uuid.UUID,
  thread_id: str,
) -> None:
  db = session_factory()
  try:
    campaign = campaign_queries.get_by_id_for_workspace(db, campaign_id, workspace_id)
    if campaign is None:
      logger.error("Campaign %s not found for execution", campaign_id)
      return

    ctx = ExecuteContext(
      campaign_id=campaign_id,
      workspace_id=workspace_id,
      thread_id=thread_id,
    )

    await run_campaign_graph(
      initial_state=_build_initial_state(campaign, thread_id),
      graph_config=_build_graph_config(session_factory, ctx),
    )

    _finalize_thread_status(session_factory, thread_id, campaign_id, workspace_id)
  except Exception as exc:
    logger.exception("Campaign execution failed for %s", campaign_id)
    db_fail = session_factory()
    try:
      campaign = campaign_queries.get_by_id_for_workspace(
        db_fail, campaign_id, workspace_id
      )
      if campaign and campaign.status in {
        CampaignStatus.RESEARCHING,
        CampaignStatus.GENERATING,
      }:
        campaign.status = CampaignStatus.FAILED
        db_fail.commit()
        _publish_status_event(campaign_id, CampaignStatus.FAILED.value)

      wf = workflow_thread_queries.get_latest_for_campaign(db_fail, campaign_id)
      if wf and wf.thread_id == thread_id:
        workflow_thread_queries.update_status(db_fail, wf, status="failed")
    finally:
      db_fail.close()
    raise exc
  finally:
    db.close()


def validate_campaign_approvable(session: Session, campaign: Campaign) -> None:
  if campaign.status != CampaignStatus.APPROVAL_PENDING:
    raise HTTPException(
      status_code=409,
      detail=f"Campaign must be in approval_pending status (current: {campaign.status.value})",
    )


def resolve_approval_thread(session: Session, campaign_id: uuid.UUID) -> str:
  thread = workflow_thread_queries.get_latest_for_campaign(
    session, campaign_id, status="awaiting_approval"
  )
  if thread is None:
    thread = workflow_thread_queries.get_latest_for_campaign(
      session, campaign_id, status="running"
    )
  if thread is None:
    raise HTTPException(
      status_code=404,
      detail="No workflow thread found for this campaign",
    )
  if thread.status not in {"awaiting_approval", "running"}:
    raise HTTPException(
      status_code=409,
      detail=f"Workflow thread is not awaiting approval (status: {thread.status})",
    )
  return thread.thread_id


async def resume_campaign_background(
  session_factory: sessionmaker,
  campaign_id: uuid.UUID,
  workspace_id: uuid.UUID,
  thread_id: str,
) -> None:
  if not is_checkpointer_enabled():
    raise RuntimeError("LangGraph checkpointer is not enabled")

  db = session_factory()
  try:
    campaign = campaign_queries.get_by_id_for_workspace(db, campaign_id, workspace_id)
    if campaign is None:
      logger.error("Campaign %s not found for resume", campaign_id)
      return

    wf = workflow_thread_queries.get_latest_for_campaign(db, campaign_id)
    if wf and wf.thread_id == thread_id:
      workflow_thread_queries.update_status(db, wf, status="running")

    ctx = ExecuteContext(
      campaign_id=campaign_id,
      workspace_id=workspace_id,
      thread_id=thread_id,
    )

    await resume_campaign_graph(
      thread_id=thread_id,
      graph_config=_build_graph_config(session_factory, ctx),
    )

    _finalize_thread_status(session_factory, thread_id, campaign_id, workspace_id)
  except Exception as exc:
    logger.exception("Campaign resume failed for %s", campaign_id)
    db_fail = session_factory()
    try:
      campaign = campaign_queries.get_by_id_for_workspace(
        db_fail, campaign_id, workspace_id
      )
      if campaign and campaign.status == CampaignStatus.APPROVAL_PENDING:
        campaign.status = CampaignStatus.FAILED
        db_fail.commit()
        _publish_status_event(campaign_id, CampaignStatus.FAILED.value)

      wf = workflow_thread_queries.get_latest_for_campaign(db_fail, campaign_id)
      if wf and wf.thread_id == thread_id:
        workflow_thread_queries.update_status(db_fail, wf, status="failed")
    finally:
      db_fail.close()
    raise exc
  finally:
    db.close()
