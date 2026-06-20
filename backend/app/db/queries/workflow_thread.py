import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.workflow_thread import WorkflowThread


def create(
  session: Session,
  *,
  campaign_id: uuid.UUID,
  thread_id: str,
  status: str | None = "running",
) -> WorkflowThread:
  thread = WorkflowThread(
    campaign_id=campaign_id,
    thread_id=thread_id,
    status=status,
  )
  session.add(thread)
  session.commit()
  session.refresh(thread)
  return thread


def update_status(
  session: Session, thread: WorkflowThread, *, status: str
) -> WorkflowThread:
  thread.status = status
  session.commit()
  session.refresh(thread)
  return thread


def get_latest_for_campaign(
  session: Session,
  campaign_id: uuid.UUID,
  *,
  status: str | None = None,
) -> WorkflowThread | None:
  stmt = select(WorkflowThread).where(WorkflowThread.campaign_id == campaign_id)
  if status is not None:
    stmt = stmt.where(WorkflowThread.status == status)
  stmt = stmt.order_by(WorkflowThread.created_at.desc()).limit(1)
  return session.scalar(stmt)
