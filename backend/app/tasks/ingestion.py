import logging
import uuid
from datetime import UTC, datetime

from app.celery_app import celery_app
from app.db.queries import document as document_queries
from app.db.queries import scheduled_job as scheduled_job_queries
from app.db.session import SessionLocal
from app.services.rag import ingest_document

logger = logging.getLogger(__name__)


@celery_app.task(
  bind=True,
  name="app.tasks.ingestion.ingest_document_task",
  autoretry_for=(Exception,),
  retry_backoff=True,
  retry_kwargs={"max_retries": 3},
)
def ingest_document_task(self, document_id: str) -> str:
  doc_uuid = uuid.UUID(document_id)
  db = SessionLocal()
  job = None
  try:
    document = document_queries.get_by_id(db, doc_uuid)
    if document is None:
      raise ValueError(f"Document {document_id} not found")

    job = scheduled_job_queries.create(
      db,
      job_type="pdf_process",
      execute_at=datetime.now(UTC),
      document_id=doc_uuid,
      celery_task_id=self.request.id,
      status="running",
    )

    ingest_document(db, document)

    if job:
      scheduled_job_queries.update_status(db, job, status="success")
    return document_id
  except Exception as exc:
    logger.exception("PDF ingestion failed for %s", document_id)
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
