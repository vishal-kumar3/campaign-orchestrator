import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.scheduled_job import ScheduledJob


def create(
  session: Session,
  *,
  job_type: str,
  execute_at: datetime,
  content_id: uuid.UUID | None = None,
  document_id: uuid.UUID | None = None,
  celery_task_id: str | None = None,
  status: str = "pending",
) -> ScheduledJob:
  job = ScheduledJob(
    content_id=content_id,
    document_id=document_id,
    job_type=job_type,
    execute_at=execute_at,
    celery_task_id=celery_task_id,
    status=status,
  )
  session.add(job)
  session.commit()
  session.refresh(job)
  return job


def get_by_id(session: Session, job_id: uuid.UUID) -> ScheduledJob | None:
  return session.get(ScheduledJob, job_id)


def update_status(
  session: Session,
  job: ScheduledJob,
  *,
  status: str,
  celery_task_id: str | None = None,
  last_error: str | None = None,
  increment_retry: bool = False,
) -> ScheduledJob:
  job.status = status
  if celery_task_id is not None:
    job.celery_task_id = celery_task_id
  if last_error is not None:
    job.last_error = last_error
  if increment_retry:
    job.retry_count += 1
  session.commit()
  session.refresh(job)
  return job


def get_active_publish_for_content(
  session: Session, content_id: uuid.UUID
) -> ScheduledJob | None:
  return session.scalar(
    select(ScheduledJob).where(
      ScheduledJob.content_id == content_id,
      ScheduledJob.job_type == "publish",
      ScheduledJob.status.in_(["pending", "running"]),
    )
  )


def list_overdue_pending(session: Session, *, now: datetime | None = None) -> list[ScheduledJob]:
  cutoff = now or datetime.now(UTC)
  return list(
    session.scalars(
      select(ScheduledJob)
      .where(
        ScheduledJob.status == "pending",
        ScheduledJob.execute_at <= cutoff,
      )
      .order_by(ScheduledJob.execute_at.asc())
    ).all()
  )


def list_for_content(session: Session, content_id: uuid.UUID) -> list[ScheduledJob]:
  return list(
    session.scalars(
      select(ScheduledJob)
      .where(ScheduledJob.content_id == content_id)
      .order_by(ScheduledJob.created_at.desc())
    ).all()
  )
