import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db.models.campaign import Campaign
from app.db.models.enums import KnowledgeScope
from app.db.models.knowledge_base import KnowledgeBase


def knowledge_bases_for_campaign(
  session: Session, campaign: Campaign
) -> list[KnowledgeBase]:
  return list(
    session.scalars(
      select(KnowledgeBase).where(
        KnowledgeBase.workspace_id == campaign.workspace_id,
        or_(
          KnowledgeBase.scope == KnowledgeScope.WORKSPACE,
          and_(
            KnowledgeBase.scope == KnowledgeScope.CAMPAIGN,
            KnowledgeBase.campaign_id == campaign.id,
          ),
        ),
      )
    ).all()
  )


def get_by_id_for_workspace(
  session: Session, knowledge_base_id: uuid.UUID, workspace_id: uuid.UUID
) -> KnowledgeBase | None:
  return session.scalar(
    select(KnowledgeBase).where(
      KnowledgeBase.id == knowledge_base_id,
      KnowledgeBase.workspace_id == workspace_id,
    )
  )


def list_for_workspace(
  session: Session, workspace_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[KnowledgeBase], int]:
  base = select(KnowledgeBase).where(KnowledgeBase.workspace_id == workspace_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(KnowledgeBase.created_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total


def create(
  session: Session,
  *,
  workspace_id: uuid.UUID,
  name: str,
  scope: KnowledgeScope,
  campaign_id: uuid.UUID | None,
) -> KnowledgeBase:
  knowledge_base = KnowledgeBase(
    workspace_id=workspace_id,
    name=name,
    scope=scope,
    campaign_id=campaign_id,
  )
  session.add(knowledge_base)
  session.commit()
  session.refresh(knowledge_base)
  return knowledge_base


def update(session: Session, knowledge_base: KnowledgeBase, **fields) -> KnowledgeBase:
  for key, value in fields.items():
    if value is not None:
      setattr(knowledge_base, key, value)
  session.commit()
  session.refresh(knowledge_base)
  return knowledge_base


def delete(session: Session, knowledge_base: KnowledgeBase) -> None:
  session.delete(knowledge_base)
  session.commit()
