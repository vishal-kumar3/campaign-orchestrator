import logging

from langchain_core.runnables import RunnableConfig

from agent.nodes._config import get_callbacks
from agent.state import CampaignGraphState

logger = logging.getLogger(__name__)


def publisher_node(state: CampaignGraphState, config: RunnableConfig) -> dict:
  callbacks = get_callbacks(config)

  run_id = callbacks["create_agent_run"]("publisher", {"content_ids": state.get("content_ids", [])})

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
      if platform != "twitter":
        callbacks["log"](
          run_id,
          "publisher",
          f"Skipping {platform} publish (deferred to Phase 4)",
        )
        continue

      content_id = item["id"]
      text = item["content"]
      try:
        callbacks["log"](run_id, "publisher", f"Publishing to Twitter ({len(text)} chars)")
        post_id = callbacks["publish_twitter"](text)
        callbacks["mark_content_published"](content_id, post_id)
        callbacks["log"](run_id, "publisher", f"Published to Twitter: {post_id}")
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
