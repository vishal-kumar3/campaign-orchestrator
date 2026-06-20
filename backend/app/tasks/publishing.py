import logging
import uuid
from datetime import UTC, datetime

from app.celery_app import celery_app
from app.db.queries import content as content_queries
from app.db.queries import scheduled_job as scheduled_job_queries
from app.db.session import SessionLocal
from app.services.publisher import PublishPayload, publish_content as publish_content_service
from app.services.rate_limiter import acquire_publish_token

logger = logging.getLogger(__name__)


@celery_app.task(
  bind=True,
  name="app.tasks.publishing.publish_content_task",
  autoretry_for=(Exception,),
  retry_backoff=True,
  retry_kwargs={"max_retries": 3},
)
def publish_content_task(self, content_id: str, job_id: str | None = None) -> str:
  content_uuid = uuid.UUID(content_id)
  db = SessionLocal()
  job = None
  try:
    content = content_queries.get_by_id(db, content_uuid)
    if content is None:
      raise ValueError(f"Content {content_id} not found")

    if job_id:
      job = scheduled_job_queries.get_by_id(db, uuid.UUID(job_id))
      if job:
        scheduled_job_queries.update_status(
          db, job, status="running", celery_task_id=self.request.id
        )

    acquire_publish_token(content.platform.value)

    external_id = publish_content_service(
      PublishPayload(
        content_id=str(content.id),
        platform=content.platform.value,
        text=content.content,
        title=content.title,
      )
    )
    content_queries.mark_published(db, content, external_post_id=external_id)

    if job:
      scheduled_job_queries.update_status(db, job, status="success")

    from app.services.scheduling import enqueue_analytics_poll

    enqueue_analytics_poll(str(content.id))
    return external_id
  except Exception as exc:
    logger.exception("Publish failed for content %s", content_id)
    content = content_queries.get_by_id(db, content_uuid)
    if content:
      content_queries.mark_failed(db, content)
    if job:
      scheduled_job_queries.update_status(
        db,
        job,
        status="failed",
        last_error=str(exc)[:500],
        increment_retry=True,
      )
    raise
  finally:
    db.close()


@celery_app.task(name="app.tasks.publishing.reconcile_overdue_jobs")
def reconcile_overdue_jobs() -> int:
  from app.services.scheduling import schedule_content_publish

  db = SessionLocal()
  dispatched = 0
  try:
    overdue = scheduled_job_queries.list_overdue_pending(db)
    for job in overdue:
      if job.job_type != "publish" or job.content_id is None:
        continue
      schedule_content_publish(db, job.content_id, job.execute_at, existing_job=job)
      dispatched += 1
    return dispatched
  finally:
    db.close()
