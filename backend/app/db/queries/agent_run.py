import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.agent_run import AgentRun
from app.db.models.enums import AgentStatus


def create(
  session: Session,
  *,
  campaign_id: uuid.UUID,
  agent_name: str,
  input_data: dict | None = None,
) -> AgentRun:
  run = AgentRun(
    campaign_id=campaign_id,
    agent_name=agent_name,
    status=AgentStatus.RUNNING,
    input=input_data,
  )
  session.add(run)
  session.commit()
  session.refresh(run)
  return run


def complete(
  session: Session,
  run: AgentRun,
  *,
  output: dict | None = None,
) -> AgentRun:
  run.status = AgentStatus.COMPLETED
  run.output = output
  run.completed_at = datetime.now(timezone.utc)
  session.commit()
  session.refresh(run)
  return run


def fail(session: Session, run: AgentRun, *, output: dict | None = None) -> AgentRun:
  run.status = AgentStatus.FAILED
  run.output = output
  run.completed_at = datetime.now(timezone.utc)
  session.commit()
  session.refresh(run)
  return run


def get_by_id_for_campaign(
  session: Session, run_id: uuid.UUID, campaign_id: uuid.UUID
) -> AgentRun | None:
  return session.scalar(
    select(AgentRun).where(
      AgentRun.id == run_id,
      AgentRun.campaign_id == campaign_id,
    )
  )


def list_for_campaign(
  session: Session, campaign_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[AgentRun], int]:
  base = select(AgentRun).where(AgentRun.campaign_id == campaign_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(AgentRun.started_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total
