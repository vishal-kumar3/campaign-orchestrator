import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import redis
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_sync_client: redis.Redis | None = None


def _channel(campaign_id: UUID | str) -> str:
  return f"campaign:{campaign_id}:logs"


def get_sync_redis() -> redis.Redis:
  global _sync_client
  if _sync_client is None:
    _sync_client = redis.from_url(settings.redis_url, decode_responses=True)
  return _sync_client


def publish_campaign_event(campaign_id: UUID | str, payload: dict[str, Any]) -> None:
  try:
    client = get_sync_redis()
    client.publish(_channel(campaign_id), json.dumps(payload, default=str))
  except Exception as exc:
    logger.warning("Failed to publish campaign event for %s: %s", campaign_id, exc)


async def subscribe_campaign_events(
  campaign_id: UUID | str,
) -> AsyncIterator[dict[str, Any]]:
  client = aioredis.from_url(settings.redis_url, decode_responses=True)
  pubsub = client.pubsub()
  await pubsub.subscribe(_channel(campaign_id))
  try:
    async for message in pubsub.listen():
      if message["type"] == "message" and message["data"]:
        yield json.loads(message["data"])
  finally:
    await pubsub.unsubscribe(_channel(campaign_id))
    await pubsub.aclose()
    await client.aclose()
