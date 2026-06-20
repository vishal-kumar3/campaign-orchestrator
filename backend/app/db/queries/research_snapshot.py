import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.research import ResearchSnapshot


def create(
  session: Session,
  *,
  campaign_id: uuid.UUID,
  summary: str | None,
  raw_data: dict | None,
) -> ResearchSnapshot:
  snapshot = ResearchSnapshot(
    campaign_id=campaign_id,
    summary=summary,
    raw_data=raw_data,
  )
  session.add(snapshot)
  session.commit()
  session.refresh(snapshot)
  return snapshot


def get_by_id(session: Session, snapshot_id: uuid.UUID) -> ResearchSnapshot | None:
  return session.get(ResearchSnapshot, snapshot_id)


def get_latest_for_campaign(
  session: Session, campaign_id: uuid.UUID
) -> ResearchSnapshot | None:
  return session.scalar(
    select(ResearchSnapshot)
    .where(ResearchSnapshot.campaign_id == campaign_id)
    .order_by(ResearchSnapshot.created_at.desc())
    .limit(1)
  )


def list_for_campaign(
  session: Session, campaign_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[ResearchSnapshot], int]:
  base = select(ResearchSnapshot).where(ResearchSnapshot.campaign_id == campaign_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(ResearchSnapshot.created_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total
