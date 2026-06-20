import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.content import CampaignContent
from app.db.models.enums import ContentStatus


def get_by_id(session: Session, content_id: uuid.UUID) -> CampaignContent | None:
  return session.get(CampaignContent, content_id)


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


def get_approved_for_campaign(
  session: Session, campaign_id: uuid.UUID
) -> list[CampaignContent]:
  return list(
    session.scalars(
      select(CampaignContent).where(
        CampaignContent.campaign_id == campaign_id,
        CampaignContent.status == ContentStatus.APPROVED,
      )
    ).all()
  )


def mark_published(
  session: Session,
  content: CampaignContent,
  *,
  external_post_id: str,
) -> CampaignContent:
  content.status = ContentStatus.PUBLISHED
  content.external_post_id = external_post_id
  content.published_at = datetime.now(UTC)
  session.commit()
  session.refresh(content)
  return content


def mark_failed(session: Session, content: CampaignContent) -> CampaignContent:
  content.status = ContentStatus.FAILED
  session.commit()
  session.refresh(content)
  return content


def bulk_update_approval(
  session: Session,
  campaign_id: uuid.UUID,
  *,
  items: list[tuple[uuid.UUID, str | None, ContentStatus, datetime | None]],
) -> None:
  for content_id, text, status, scheduled_at in items:
    content = get_by_id_for_campaign(session, content_id, campaign_id)
    if content is None:
      raise ValueError(f"Content {content_id} not found for campaign")
    content.status = status
    if text is not None:
      content.content = text
    if scheduled_at is not None:
      content.scheduled_at = scheduled_at
  session.commit()


def create(
  session: Session,
  *,
  campaign_id: uuid.UUID,
  platform,
  title: str | None,
  content: str,
  status: ContentStatus | None,
  variant: str = "A",
) -> CampaignContent:
  campaign_content = CampaignContent(
    campaign_id=campaign_id,
    platform=platform,
    title=title,
    content=content,
    status=status or ContentStatus.DRAFT,
    variant=variant,
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


def list_all_for_campaign(session: Session, campaign_id: uuid.UUID) -> list[CampaignContent]:
  return list(
    session.scalars(
      select(CampaignContent)
      .where(CampaignContent.campaign_id == campaign_id)
      .order_by(CampaignContent.platform.asc(), CampaignContent.variant.asc())
    ).all()
  )


def get_by_ids_for_campaign(
  session: Session, campaign_id: uuid.UUID, content_ids: list[uuid.UUID]
) -> list[CampaignContent]:
  return list(
    session.scalars(
      select(CampaignContent).where(
        CampaignContent.campaign_id == campaign_id,
        CampaignContent.id.in_(content_ids),
      )
    ).all()
  )


def set_scheduled_at(
  session: Session, content: CampaignContent, scheduled_at: datetime
) -> CampaignContent:
  content.scheduled_at = scheduled_at
  session.commit()
  session.refresh(content)
  return content


def update_engagement_metrics(
  session: Session, content: CampaignContent, metrics: dict
) -> CampaignContent:
  content.engagement_metrics = metrics
  session.commit()
  session.refresh(content)
  return content
