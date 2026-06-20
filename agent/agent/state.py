from typing import Any, Callable, TypedDict

from typing_extensions import NotRequired


class AgentCallbacks(TypedDict):
  create_agent_run: Callable[[str, dict | None], str]
  complete_agent_run: Callable[[str, dict | None], None]
  fail_agent_run: Callable[[str, dict | None], None]
  log: Callable[..., None]
  create_research_snapshot: Callable[[str, dict | None], str]
  get_research_summary: Callable[[str], str]
  create_content: Callable[[str, str | None, str, str], str]
  retrieve_brand_context: Callable[[str, str, int], list[dict[str, Any]]]
  transition_campaign_status: Callable[[str, str], None]
  get_approved_contents: Callable[[], list[dict[str, Any]]]
  mark_content_published: Callable[[str, str], None]
  mark_content_failed: Callable[[str, str], None]
  publish_content: Callable[[str, str, str, str | None], str]
  enqueue_scheduled_publish: Callable[[str, str], str]
  get_engagement_recommendations: Callable[[str, list[str]], dict[str, list[dict[str, Any]]]]
  get_contents_by_ids: Callable[[list[str]], list[dict[str, Any]]]
  set_content_scheduled_at: Callable[[str, str], None]


class AgentSettings(TypedDict):
  google_api_key: str
  chat_model: str
  tavily_api_key: str
  retrieve_default_k: int
  content_ab_variants: int


class GraphConfigurable(TypedDict):
  callbacks: AgentCallbacks
  settings: AgentSettings


class CampaignGraphState(TypedDict):
  campaign_id: str
  workspace_id: str
  thread_id: str
  objective: str
  target_audience: str | None
  platforms: list[str]
  knowledge_base_id: str
  competitor_urls: list[str]
  research_snapshot_id: str | None
  content_ids: list[str]
  approved_content_ids: NotRequired[list[str]]
  error: NotRequired[str | None]
