import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.queries import scheduled_job as scheduled_job_queries
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def analytics_poll_delay() -> timedelta:
  if settings.app_env == "development":
    return timedelta(seconds=settings.analytics_poll_delay_seconds_dev)
  return timedelta(hours=settings.analytics_poll_delay_hours)


def schedule_content_publish(
  db: Session,
  content_id: uuid.UUID,
  execute_at: datetime,
  *,
  existing_job=None,
) -> str:
  from app.tasks.publishing import publish_content_task

  active = scheduled_job_queries.get_active_publish_for_content(db, content_id)
  if active and (existing_job is None or active.id != existing_job.id):
    return str(active.id)

  if existing_job:
    job = existing_job
    scheduled_job_queries.update_status(db, job, status="pending")
  else:
    job = scheduled_job_queries.create(
      db,
      job_type="publish",
      execute_at=execute_at,
      content_id=content_id,
    )

  result = publish_content_task.apply_async(
    args=[str(content_id), str(job.id)],
    eta=execute_at,
  )
  scheduled_job_queries.update_status(
    db, job, status="pending", celery_task_id=result.id
  )
  return str(job.id)


def enqueue_immediate_publish(db: Session, content_id: uuid.UUID) -> str:
  return schedule_content_publish(db, content_id, datetime.now(UTC))


def enqueue_analytics_poll(content_id: str) -> str:
  from app.tasks.analytics import poll_content_analytics_task

  db = SessionLocal()
  try:
    execute_at = datetime.now(UTC) + analytics_poll_delay()
    job = scheduled_job_queries.create(
      db,
      job_type="analytics_poll",
      execute_at=execute_at,
      content_id=uuid.UUID(content_id),
    )
    result = poll_content_analytics_task.apply_async(
      args=[content_id, str(job.id)],
      eta=execute_at,
    )
    scheduled_job_queries.update_status(
      db, job, status="pending", celery_task_id=result.id
    )
    return str(job.id)
  finally:
    db.close()
