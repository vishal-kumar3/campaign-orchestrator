import logging

from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient

from agent.nodes._config import get_callbacks, get_settings
from agent.state import CampaignGraphState

logger = logging.getLogger(__name__)


def _domain_from_url(url: str) -> str:
  from urllib.parse import urlparse

  parsed = urlparse(url)
  return parsed.netloc or url


def research_node(state: CampaignGraphState, config: RunnableConfig) -> dict:
  callbacks = get_callbacks(config)
  settings = get_settings(config)

  run_id = callbacks["create_agent_run"](
    "research",
    {
      "objective": state["objective"],
      "competitor_urls": state["competitor_urls"],
    },
  )

  try:
    callbacks["log"](run_id, "research", "Starting competitor and market research")

    tavily_hits: list[dict] = []
    if settings["tavily_api_key"]:
      client = TavilyClient(api_key=settings["tavily_api_key"])

      for url in state["competitor_urls"]:
        domain = _domain_from_url(url)
        callbacks["log"](run_id, "research", f"Researching competitor: {domain}")
        result = client.search(
          query=f"site:{domain} products messaging positioning",
          max_results=3,
        )
        tavily_hits.append({"url": url, "domain": domain, "results": result})

      audience = state.get("target_audience") or "general audience"
      market_query = f"{state['objective']} marketing trends for {audience}"
      callbacks["log"](run_id, "research", "Searching market context")
      market_result = client.search(query=market_query, max_results=5)
      tavily_hits.append({"query": market_query, "results": market_result})

      reddit_query = f"site:reddit.com {state['objective']} sentiment discussion"
      callbacks["log"](run_id, "research", "Searching Reddit sentiment")
      reddit_result = client.search(query=reddit_query, max_results=5)
      tavily_hits.append({"query": reddit_query, "results": reddit_result})

      twitter_query = f"{state['objective']} twitter X sentiment reactions"
      callbacks["log"](run_id, "research", "Searching Twitter/X sentiment")
      twitter_result = client.search(query=twitter_query, max_results=5)
      tavily_hits.append({"query": twitter_query, "results": twitter_result})
    else:
      callbacks["log"](
        run_id,
        "research",
        "Tavily API key not configured; using objective-only summary",
        "warning",
      )

    llm = ChatGoogleGenerativeAI(
      model=settings["chat_model"],
      google_api_key=settings["google_api_key"],
      temperature=0.4,
    )

    research_context = "\n\n".join(str(hit) for hit in tavily_hits) or (
      "No external research data available."
    )

    prompt = f"""You are a marketing research analyst. Synthesize findings for a campaign.

Campaign objective: {state['objective']}
Target audience: {state.get('target_audience') or 'Not specified'}
Competitor URLs: {', '.join(state['competitor_urls']) or 'None'}

Research data:
{research_context[:12000]}

Write a concise research summary with:
1. Key competitor positioning gaps
2. Audience insights and angles (include Reddit/Twitter sentiment when present)
3. Recommended content hooks for social posts

Keep the summary under 800 words."""

    callbacks["log"](run_id, "research", "Synthesizing research summary with Gemini")
    response = llm.invoke(prompt)
    summary = (
      response.content if isinstance(response.content, str) else str(response.content)
    )

    snapshot_id = callbacks["create_research_snapshot"](
      summary,
      {"tavily_hits": tavily_hits},
    )

    callbacks["complete_agent_run"](
      run_id,
      {"snapshot_id": snapshot_id, "source_count": len(tavily_hits)},
    )
    callbacks["log"](run_id, "research", "Research complete")
    callbacks["transition_campaign_status"]("researching", "generating")

    return {"research_snapshot_id": snapshot_id}
  except Exception as exc:
    logger.exception("Research node failed")
    callbacks["fail_agent_run"](run_id, {"error": str(exc)})
    callbacks["log"](run_id, "research", f"Research failed: {exc}", "error")
    raise
