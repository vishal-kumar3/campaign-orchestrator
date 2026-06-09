from sqlalchemy import and_, or_, select
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
