import uuid

from sqlalchemy.orm import Session

from app.db.models.enums import ContentPlatform, ContentStatus
from app.db.queries import content as content_queries
from app.schemas.analytics import (
  CampaignAnalyticsResponse,
  ContentAnalyticsItem,
  PlatformSummary,
  VariantComparison,
)


def build_campaign_analytics(
  session: Session, campaign_id: uuid.UUID
) -> CampaignAnalyticsResponse:
  items = content_queries.list_all_for_campaign(session, campaign_id)

  contents: list[ContentAnalyticsItem] = []
  by_platform: dict[str, dict] = {}
  variant_rates: dict[tuple[str, str], list[float]] = {}

  total_impressions = 0
  total_engagements = 0
  total_clicks = 0

  for item in items:
    metrics = item.engagement_metrics or {}
    impressions = int(metrics.get("impressions", 0))
    engagements = int(metrics.get("likes", metrics.get("engagements", 0)))
    clicks = int(metrics.get("clicks", 0))
    engagement_rate = float(metrics.get("engagement_rate", 0.0))
    ctr = float(metrics.get("ctr", 0.0))

    if item.status == ContentStatus.PUBLISHED:
      total_impressions += impressions
      total_engagements += engagements
      total_clicks += clicks

      platform_key = item.platform.value
      bucket = by_platform.setdefault(
        platform_key,
        {"impressions": 0, "engagements": 0, "clicks": 0, "rates": [], "ctrs": []},
      )
      bucket["impressions"] += impressions
      bucket["engagements"] += engagements
      bucket["clicks"] += clicks
      bucket["rates"].append(engagement_rate)
      bucket["ctrs"].append(ctr)

      variant_rates.setdefault((platform_key, item.variant), []).append(engagement_rate)

    contents.append(
      ContentAnalyticsItem(
        content_id=item.id,
        platform=item.platform,
        variant=item.variant,
        status=item.status,
        engagement_metrics=metrics,
        scheduled_at=item.scheduled_at,
        published_at=item.published_at,
        external_post_id=item.external_post_id,
      )
    )

  platform_summaries: list[PlatformSummary] = []
  for platform_key, bucket in by_platform.items():
    impressions = bucket["impressions"]
    engagements = bucket["engagements"]
    clicks = bucket["clicks"]
    rates = bucket["rates"] or [0.0]
    ctrs = bucket["ctrs"] or [0.0]
    platform_summaries.append(
      PlatformSummary(
        platform=ContentPlatform(platform_key),
        impressions=impressions,
        engagements=engagements,
        clicks=clicks,
        engagement_rate=round(sum(rates) / len(rates), 4),
        ctr=round(sum(ctrs) / len(ctrs), 4),
      )
    )

  variant_comparisons: list[VariantComparison] = []
  platforms_seen = {p for p, _ in variant_rates}
  for platform_key in platforms_seen:
    a_rates = variant_rates.get((platform_key, "A"), [])
    b_rates = variant_rates.get((platform_key, "B"), [])
    a_avg = sum(a_rates) / len(a_rates) if a_rates else 0.0
    b_avg = sum(b_rates) / len(b_rates) if b_rates else 0.0
    winner = "A" if a_avg >= b_avg else "B"
    if not a_rates and not b_rates:
      winner = "tie"
    variant_comparisons.append(
      VariantComparison(
        platform=ContentPlatform(platform_key),
        variant_a_rate=round(a_avg, 4),
        variant_b_rate=round(b_avg, 4),
        winner=winner,
      )
    )

  totals = {
    "impressions": total_impressions,
    "engagements": total_engagements,
    "clicks": total_clicks,
    "engagement_rate": round(
      total_engagements / total_impressions, 4
    )
    if total_impressions
    else 0.0,
    "ctr": round(total_clicks / total_impressions, 4) if total_impressions else 0.0,
  }

  return CampaignAnalyticsResponse(
    campaign_id=campaign_id,
    totals=totals,
    by_platform=platform_summaries,
    variants=variant_comparisons,
    contents=contents,
  )
