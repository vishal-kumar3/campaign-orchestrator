import logging
from datetime import UTC, datetime, timedelta

from langchain_core.runnables import RunnableConfig

from agent.nodes._config import get_callbacks
from agent.state import CampaignGraphState

logger = logging.getLogger(__name__)


def _next_occurrence(post_day: int, post_hour: int, *, now: datetime | None = None) -> datetime:
  current = now or datetime.now(UTC)
  candidate = current.replace(hour=post_hour, minute=0, second=0, microsecond=0)
  days_ahead = (post_day - candidate.weekday()) % 7
  if days_ahead == 0 and candidate <= current:
    days_ahead = 7
  return candidate + timedelta(days=days_ahead)


def scheduler_node(state: CampaignGraphState, config: RunnableConfig) -> dict:
  callbacks = get_callbacks(config)

  run_id = callbacks["create_agent_run"](
    "scheduler",
    {"content_ids": state.get("content_ids", []), "platforms": state["platforms"]},
  )

  try:
    callbacks["log"](run_id, "scheduler", "Analyzing historical engagement for optimal times")
    recommendations = callbacks["get_engagement_recommendations"](
      state["workspace_id"],
      state["platforms"],
    )

    content_ids = state.get("content_ids", [])
    if not content_ids:
      callbacks["log"](run_id, "scheduler", "No content to schedule", "warning")
      callbacks["complete_agent_run"](run_id, {"scheduled": 0})
      return {}

    contents = callbacks["get_contents_by_ids"](content_ids)
    scheduled_count = 0

    for item in contents:
      platform = item["platform"]
      slots = recommendations.get(platform, [])
      if not slots:
        scheduled_at = datetime.now(UTC) + timedelta(hours=1)
        callbacks["log"](
          run_id,
          "scheduler",
          f"No engagement data for {platform}; defaulting to +1h",
          "warning",
        )
      else:
        best = slots[0]
        scheduled_at = _next_occurrence(best["post_day"], best["post_hour"])
        callbacks["log"](
          run_id,
          "scheduler",
          f"Recommended {platform} variant {item.get('variant', 'A')} at "
          f"{scheduled_at.isoformat()} (score={best['score']:.3f})",
        )

      callbacks["set_content_scheduled_at"](item["id"], scheduled_at.isoformat())
      scheduled_count += 1

    callbacks["complete_agent_run"](run_id, {"scheduled": scheduled_count})
    callbacks["log"](run_id, "scheduler", f"Scheduled {scheduled_count} content pieces")
    return {}
  except Exception as exc:
    logger.exception("Scheduler node failed")
    callbacks["fail_agent_run"](run_id, {"error": str(exc)})
    callbacks["log"](run_id, "scheduler", f"Scheduler failed: {exc}", "error")
    raise
