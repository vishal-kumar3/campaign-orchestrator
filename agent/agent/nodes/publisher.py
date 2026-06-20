import logging
from datetime import UTC, datetime

from langchain_core.runnables import RunnableConfig

from agent.nodes._config import get_callbacks
from agent.state import CampaignGraphState

logger = logging.getLogger(__name__)

_PUBLISHABLE_PLATFORMS = {"twitter", "linkedin", "email"}


def publisher_node(state: CampaignGraphState, config: RunnableConfig) -> dict:
  callbacks = get_callbacks(config)

  run_id = callbacks["create_agent_run"](
    "publisher", {"content_ids": state.get("content_ids", [])}
  )

  try:
    callbacks["log"](run_id, "publisher", "Starting publisher")
    approved = callbacks["get_approved_contents"]()

    if not approved:
      callbacks["log"](
        run_id,
        "publisher",
        "No approved content to publish",
        "warning",
      )
      return {}

    for item in approved:
      platform = item["platform"]
      content_id = item["id"]

      if platform == "blog":
        callbacks["log"](run_id, "publisher", "Blog content is export-only; skipping publish")
        continue

      if platform not in _PUBLISHABLE_PLATFORMS:
        callbacks["log"](run_id, "publisher", f"Skipping unsupported platform: {platform}")
        continue

      scheduled_at_raw = item.get("scheduled_at")
      scheduled_at = None
      if scheduled_at_raw:
        scheduled_at = datetime.fromisoformat(scheduled_at_raw.replace("Z", "+00:00"))

      if scheduled_at and scheduled_at > datetime.now(UTC):
        callbacks["log"](
          run_id,
          "publisher",
          f"Scheduling {platform} publish for {scheduled_at.isoformat()}",
        )
        callbacks["enqueue_scheduled_publish"](content_id, scheduled_at.isoformat())
        continue

      try:
        callbacks["log"](run_id, "publisher", f"Publishing to {platform}")
        post_id = callbacks["publish_content"](
          platform,
          content_id,
          item["content"],
          item.get("title"),
        )
        callbacks["mark_content_published"](content_id, post_id)
        callbacks["log"](run_id, "publisher", f"Published to {platform}: {post_id}")
      except Exception as exc:
        logger.exception("Failed to publish content %s", content_id)
        callbacks["mark_content_failed"](content_id, str(exc))
        callbacks["log"](
          run_id,
          "publisher",
          f"Failed to publish {content_id}: {exc}",
          "error",
        )

    callbacks["transition_campaign_status"]("approval_pending", "completed")
    callbacks["complete_agent_run"](run_id, {"published": True})
    callbacks["log"](run_id, "publisher", "Publisher finished")
    return {}
  except Exception as exc:
    logger.exception("Publisher node failed")
    callbacks["fail_agent_run"](run_id, {"error": str(exc)})
    callbacks["log"](run_id, "publisher", f"Publisher failed: {exc}", "error")
    raise
