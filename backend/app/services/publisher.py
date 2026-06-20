import logging
import uuid
from typing import Protocol

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class PublisherError(Exception):
  pass


class PublishPayload(BaseModel):
  content_id: str
  platform: str
  text: str
  title: str | None = None


class Publisher(Protocol):
  def publish(self, payload: PublishPayload) -> str: ...


class TwitterPublisher:
  def publish(self, payload: PublishPayload) -> str:
    if settings.publisher_dry_run:
      post_id = f"dry-run-{uuid.uuid4()}"
      logger.info("DRY RUN tweet (%d chars) -> %s", len(payload.text), post_id)
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
      response = client.create_tweet(text=payload.text)
      post_id = str(response.data["id"])
      logger.info("Published tweet %s", post_id)
      return post_id
    except Exception as exc:
      raise PublisherError(str(exc)) from exc


class LinkedInPublisher:
  def publish(self, payload: PublishPayload) -> str:
    if settings.publisher_dry_run:
      post_id = f"dry-run-li-{uuid.uuid4()}"
      logger.info("DRY RUN LinkedIn (%d chars) -> %s", len(payload.text), post_id)
      return post_id

    if not settings.linkedin_access_token:
      raise PublisherError("LinkedIn access token is not configured")

    try:
      response = httpx.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
          "Authorization": f"Bearer {settings.linkedin_access_token}",
          "Content-Type": "application/json",
          "X-Restli-Protocol-Version": "2.0.0",
        },
        json={
          "author": "urn:li:person:PLACEHOLDER",
          "lifecycleState": "PUBLISHED",
          "specificContent": {
            "com.linkedin.ugc.ShareContent": {
              "shareCommentary": {"text": payload.text},
              "shareMediaCategory": "NONE",
            }
          },
          "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        },
        timeout=30.0,
      )
      response.raise_for_status()
      return response.headers.get("x-restli-id", str(uuid.uuid4()))
    except Exception as exc:
      raise PublisherError(str(exc)) from exc


class MailchimpPublisher:
  def publish(self, payload: PublishPayload) -> str:
    if settings.publisher_dry_run:
      post_id = f"dry-run-mc-{uuid.uuid4()}"
      logger.info("DRY RUN Mailchimp email -> %s", post_id)
      return post_id

    if not all(
      [settings.mailchimp_api_key, settings.mailchimp_server_prefix, settings.mailchimp_list_id]
    ):
      raise PublisherError("Mailchimp credentials are not configured")

    try:
      base = f"https://{settings.mailchimp_server_prefix}.api.mailchimp.com/3.0"
      auth = ("anystring", settings.mailchimp_api_key)
      campaign_resp = httpx.post(
        f"{base}/campaigns",
        auth=auth,
        json={
          "type": "regular",
          "recipients": {"list_id": settings.mailchimp_list_id},
          "settings": {
            "subject_line": payload.title or "Campaign Email",
            "title": payload.title or "Campaign Email",
            "from_name": "Campaign Orchestrator",
            "reply_to": "noreply@example.com",
          },
        },
        timeout=30.0,
      )
      campaign_resp.raise_for_status()
      campaign_id = campaign_resp.json()["id"]
      content_resp = httpx.put(
        f"{base}/campaigns/{campaign_id}/content",
        auth=auth,
        json={"html": payload.text},
        timeout=30.0,
      )
      content_resp.raise_for_status()
      return str(campaign_id)
    except Exception as exc:
      raise PublisherError(str(exc)) from exc


_PUBLISHERS: dict[str, Publisher] = {
  "twitter": TwitterPublisher(),
  "linkedin": LinkedInPublisher(),
  "email": MailchimpPublisher(),
}


def get_publisher(platform: str) -> Publisher:
  publisher = _PUBLISHERS.get(platform)
  if publisher is None:
    raise PublisherError(f"No publisher configured for platform: {platform}")
  return publisher


def publish_content(payload: PublishPayload) -> str:
  return get_publisher(payload.platform).publish(payload)


def publish_twitter_post(text: str) -> str:
  return publish_content(
    PublishPayload(content_id="", platform="twitter", text=text)
  )
