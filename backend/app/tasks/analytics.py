import hashlib
import logging
import uuid
from datetime import UTC, datetime

from app.celery_app import celery_app
from app.core.config import settings
from app.db.queries import agent_run as agent_run_queries
from app.db.queries import content as content_queries
from app.db.queries import scheduled_job as scheduled_job_queries
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _mock_metrics(content_id: uuid.UUID) -> dict:
  digest = hashlib.sha256(str(content_id).encode()).hexdigest()
  impressions = 800 + int(digest[:4], 16) % 4000
  likes = max(1, int(impressions * (0.02 + (int(digest[4:6], 16) % 80) / 1000)))
  clicks = max(0, int(likes * (0.1 + (int(digest[6:8], 16) % 30) / 100)))
  engagement_rate = round(likes / impressions, 4) if impressions else 0.0
  ctr = round(clicks / impressions, 4) if impressions else 0.0
  return {
    "impressions": impressions,
    "likes": likes,
    "clicks": clicks,
    "engagement_rate": engagement_rate,
    "ctr": ctr,
  }


@celery_app.task(
  bind=True,
  name="app.tasks.analytics.poll_content_analytics_task",
  autoretry_for=(Exception,),
  retry_backoff=True,
  retry_kwargs={"max_retries": 3},
)
def poll_content_analytics_task(self, content_id: str, job_id: str | None = None) -> dict:
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

    metrics = _mock_metrics(content_uuid)
    content_queries.update_engagement_metrics(db, content, metrics)

    run = agent_run_queries.create(
      db,
      campaign_id=content.campaign_id,
      agent_name="analytics",
      input_data={"content_id": content_id},
    )
    agent_run_queries.complete(
      db,
      run,
      output={"metrics": metrics},
    )

    if job:
      scheduled_job_queries.update_status(db, job, status="success")
    return metrics
  except Exception as exc:
    logger.exception("Analytics poll failed for %s", content_id)
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
