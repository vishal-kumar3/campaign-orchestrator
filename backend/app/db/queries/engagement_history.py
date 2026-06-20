import random
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.engagement_history import EngagementHistory
from app.db.models.enums import ContentPlatform

POST_TYPES = ("promotional", "educational", "entertainment")


@dataclass
class EngagementSlot:
  post_day: int
  post_hour: int
  score: float
  impressions: int
  engagements: int


def count_for_workspace(session: Session, workspace_id: uuid.UUID) -> int:
  return (
    session.scalar(
      select(func.count())
      .select_from(EngagementHistory)
      .where(EngagementHistory.workspace_id == workspace_id)
    )
    or 0
  )


def seed_for_workspace(session: Session, workspace_id: uuid.UUID, *, rows: int = 200) -> int:
  if count_for_workspace(session, workspace_id) > 0:
    return 0

  rng = random.Random(str(workspace_id))
  platforms = list(ContentPlatform)
  batch: list[EngagementHistory] = []

  for _ in range(rows):
    platform = rng.choice(platforms)
    post_day = rng.randint(0, 6)
    post_hour = rng.randint(8, 20)
    post_type = rng.choice(POST_TYPES)
    impressions = rng.randint(500, 5000)
    engagement_rate = rng.uniform(0.02, 0.12)
    engagements = max(1, int(impressions * engagement_rate))
    clicks = max(0, int(engagements * rng.uniform(0.1, 0.4)))
    batch.append(
      EngagementHistory(
        workspace_id=workspace_id,
        platform=platform,
        post_hour=post_hour,
        post_day=post_day,
        post_type=post_type,
        impressions=impressions,
        engagements=engagements,
        clicks=clicks,
      )
    )

  session.add_all(batch)
  session.commit()
  return len(batch)


def aggregate_best_slots(
  session: Session,
  workspace_id: uuid.UUID,
  platform: ContentPlatform,
  *,
  limit: int = 5,
) -> list[EngagementSlot]:
  rows = session.execute(
    select(
      EngagementHistory.post_day,
      EngagementHistory.post_hour,
      func.sum(EngagementHistory.impressions).label("impressions"),
      func.sum(EngagementHistory.engagements).label("engagements"),
    )
    .where(
      EngagementHistory.workspace_id == workspace_id,
      EngagementHistory.platform == platform,
    )
    .group_by(EngagementHistory.post_day, EngagementHistory.post_hour)
    .order_by(
      (func.sum(EngagementHistory.engagements) / func.nullif(func.sum(EngagementHistory.impressions), 0)).desc()
    )
    .limit(limit)
  ).all()

  slots: list[EngagementSlot] = []
  for row in rows:
    impressions = int(row.impressions or 0)
    engagements = int(row.engagements or 0)
    score = engagements / impressions if impressions > 0 else 0.0
    slots.append(
      EngagementSlot(
        post_day=int(row.post_day),
        post_hour=int(row.post_hour),
        score=score,
        impressions=impressions,
        engagements=engagements,
      )
    )
  return slots
