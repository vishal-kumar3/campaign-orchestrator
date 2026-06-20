import logging
import time

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_LIMITS = {
  "twitter": (10, 60),
  "linkedin": (5, 60),
  "mailchimp": (3, 60),
}


def _get_redis() -> redis.Redis:
  return redis.from_url(settings.redis_url, decode_responses=True)


def acquire_publish_token(platform: str, *, block_seconds: float = 30.0) -> None:
  limit, window = _LIMITS.get(platform, (5, 60))
  key = f"rate_limit:publish:{platform}"
  client = _get_redis()
  deadline = time.time() + block_seconds

  while time.time() < deadline:
    current = client.incr(key)
    if current == 1:
      client.expire(key, window)
    if current <= limit:
      return
    time.sleep(0.5)

  logger.warning("Rate limit exceeded for %s; proceeding anyway", platform)
