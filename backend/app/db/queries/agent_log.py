import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.agent_log import AgentLog
from app.db.models.agent_run import AgentRun
from app.db.models.enums import LogLevel


def create(
  session: Session,
  *,
  run_id: uuid.UUID,
  node_name: str,
  message: str,
  level: LogLevel = LogLevel.INFO,
  metadata: dict | None = None,
) -> AgentLog:
  log = AgentLog(
    run_id=run_id,
    node_name=node_name,
    level=level,
    message=message,
    metadata_=metadata,
  )
  session.add(log)
  session.commit()
  session.refresh(log)
  return log


def list_for_run(
  session: Session, run_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[AgentLog], int]:
  base = select(AgentLog).where(AgentLog.run_id == run_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(AgentLog.created_at.asc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total


def list_for_campaign(
  session: Session, campaign_id: uuid.UUID, *, limit: int
) -> list[AgentLog]:
  return list(
    session.scalars(
      select(AgentLog)
      .join(AgentRun, AgentLog.run_id == AgentRun.id)
      .where(AgentRun.campaign_id == campaign_id)
      .order_by(AgentLog.created_at.asc())
      .limit(limit)
    ).all()
  )
