import logging
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class PublisherError(Exception):
  pass


def publish_twitter_post(text: str) -> str:
  if settings.publisher_dry_run:
    post_id = f"dry-run-{uuid.uuid4()}"
    logger.info("DRY RUN tweet (%d chars) -> %s", len(text), post_id)
    return post_id

  if not all(
    [
      settings.twitter_api_key,
      settings.twitter_api_secret,
      settings.twitter_access_token,
      settings.twitter_access_token_secret,
    ]
  ):
    raise PublisherError("Twitter credentials are not configured")

  try:
    import tweepy

    client = tweepy.Client(
      consumer_key=settings.twitter_api_key,
      consumer_secret=settings.twitter_api_secret,
      access_token=settings.twitter_access_token,
      access_token_secret=settings.twitter_access_token_secret,
    )
    response = client.create_tweet(text=text)
    post_id = str(response.data["id"])
    logger.info("Published tweet %s", post_id)
    return post_id
  except Exception as exc:
    raise PublisherError(str(exc)) from exc
