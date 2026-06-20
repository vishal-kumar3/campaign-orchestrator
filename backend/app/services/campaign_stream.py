import asyncio
import json
import logging
from collections.abc import AsyncIterator
from uuid import UUID

from app.core.config import settings
from app.db.queries import agent_log as agent_log_queries
from app.services.event_bus import subscribe_campaign_events

logger = logging.getLogger(__name__)


def _log_to_sse_event(log_row) -> dict:
  return {
    "type": "log",
    "id": str(log_row.id),
    "run_id": str(log_row.run_id),
    "node_name": log_row.node_name,
    "level": log_row.level.value,
    "message": log_row.message,
    "created_at": log_row.created_at.isoformat(),
  }


async def campaign_event_stream(
  session_factory,
  campaign_id: UUID,
) -> AsyncIterator[str]:
  db = session_factory()
  try:
    replay_logs = agent_log_queries.list_for_campaign(
      db,
      campaign_id,
      limit=settings.sse_replay_log_limit,
    )
  finally:
    db.close()

  for log_row in replay_logs:
    yield f"data: {json.dumps(_log_to_sse_event(log_row), default=str)}\n\n"

  queue: asyncio.Queue[dict | None] = asyncio.Queue()

  async def redis_listener() -> None:
    try:
      async for message in subscribe_campaign_events(campaign_id):
        await queue.put(message)
    except asyncio.CancelledError:
      raise
    except Exception as exc:
      logger.warning("Redis listener error for campaign %s: %s", campaign_id, exc)
    finally:
      await queue.put(None)

  listener_task = asyncio.create_task(redis_listener())
  try:
    while True:
      try:
        message = await asyncio.wait_for(
          queue.get(),
          timeout=settings.sse_heartbeat_seconds,
        )
        if message is None:
          break
        yield f"data: {json.dumps(message, default=str)}\n\n"
      except asyncio.TimeoutError:
        yield ": ping\n\n"
  finally:
    listener_task.cancel()
    try:
      await listener_task
    except asyncio.CancelledError:
      pass
