from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
  "campaign_orchestrator",
  broker=settings.celery_broker_url,
  backend=settings.celery_result_backend,
  include=[
    "app.tasks.ingestion",
    "app.tasks.publishing",
    "app.tasks.analytics",
  ],
)

celery_app.conf.update(
  task_serializer="json",
  accept_content=["json"],
  result_serializer="json",
  timezone=settings.default_timezone,
  enable_utc=True,
  task_acks_late=True,
  task_default_retry_delay=60,
  beat_schedule={
    "reconcile-overdue-jobs": {
      "task": "app.tasks.publishing.reconcile_overdue_jobs",
      "schedule": crontab(minute="*/5"),
    },
  },
)
