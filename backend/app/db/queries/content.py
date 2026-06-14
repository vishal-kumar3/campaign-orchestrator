import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.content import CampaignContent
from app.db.models.enums import ContentStatus


def get_by_id_for_campaign(
  session: Session, content_id: uuid.UUID, campaign_id: uuid.UUID
) -> CampaignContent | None:
  return session.scalar(
    select(CampaignContent).where(
      CampaignContent.id == content_id,
      CampaignContent.campaign_id == campaign_id,
    )
  )


def list_for_campaign(
  session: Session, campaign_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[CampaignContent], int]:
  base = select(CampaignContent).where(CampaignContent.campaign_id == campaign_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(CampaignContent.created_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total


def create(
  session: Session,
  *,
  campaign_id: uuid.UUID,
  platform,
  title: str | None,
  content: str,
  status: ContentStatus | None,
) -> CampaignContent:
  campaign_content = CampaignContent(
    campaign_id=campaign_id,
    platform=platform,
    title=title,
    content=content,
    status=status or ContentStatus.DRAFT,
  )
  session.add(campaign_content)
  session.commit()
  session.refresh(campaign_content)
  return campaign_content


def update(session: Session, campaign_content: CampaignContent, **fields) -> CampaignContent:
  for key, value in fields.items():
    if value is not None:
      setattr(campaign_content, key, value)
  session.commit()
  session.refresh(campaign_content)
  return campaign_content


def delete(session: Session, campaign_content: CampaignContent) -> None:
  session.delete(campaign_content)
  session.commit()
