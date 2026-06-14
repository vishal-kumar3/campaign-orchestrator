import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.campaign import Campaign
from app.db.models.enums import CampaignStatus


def get_by_id_for_workspace(
  session: Session, campaign_id: uuid.UUID, workspace_id: uuid.UUID
) -> Campaign | None:
  return session.scalar(
    select(Campaign).where(
      Campaign.id == campaign_id,
      Campaign.workspace_id == workspace_id,
    )
  )


def list_for_workspace(
  session: Session, workspace_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[Campaign], int]:
  base = select(Campaign).where(Campaign.workspace_id == workspace_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total


def create(
  session: Session,
  *,
  workspace_id: uuid.UUID,
  title: str,
  objective: str,
  target_audience: str | None,
  region: str | None,
  platforms: list | None,
) -> Campaign:
  campaign = Campaign(
    workspace_id=workspace_id,
    title=title,
    objective=objective,
    target_audience=target_audience,
    region=region,
    platforms=platforms,
    status=CampaignStatus.DRAFT,
  )
  session.add(campaign)
  session.commit()
  session.refresh(campaign)
  return campaign


def update(session: Session, campaign: Campaign, **fields) -> Campaign:
  for key, value in fields.items():
    if value is not None:
      setattr(campaign, key, value)
  session.commit()
  session.refresh(campaign)
  return campaign


def delete(session: Session, campaign: Campaign) -> None:
  session.delete(campaign)
  session.commit()
