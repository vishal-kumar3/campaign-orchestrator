import logging

from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.nodes._config import get_callbacks, get_settings
from agent.state import CampaignGraphState

logger = logging.getLogger(__name__)

_PLATFORM_PROMPTS = {
  "twitter": """Write a single Twitter/X post (max 280 characters).
Tone: punchy, scroll-stopping, on-brand.
Return only the post text, no quotes or labels.""",
  "linkedin": """Write a LinkedIn post (150-300 words).
Tone: professional, insightful, thought-leadership.
Include a short hook opening line. Return only the post text.""",
  "email": """Write a marketing email as HTML (use simple tags: h1, p, ul, strong).
First line must be "Subject: <subject line>" on its own line, then a blank line, then HTML body.
Tone: professional newsletter.""",
  "blog": """Write a blog post in markdown (800-1200 words).
Start with a single # title line, then the body with ## subheadings.
Tone: authoritative, educational, on-brand.""",
}

_VARIANT_SUFFIX = {
  "A": "",
  "B": "\n\nCreate an alternate angle: more provocative hook and data-driven framing.",
}


def content_node(state: CampaignGraphState, config: RunnableConfig) -> dict:
  callbacks = get_callbacks(config)
  settings = get_settings(config)
  ab_variants = settings.get("content_ab_variants", 2)

  snapshot_id = state.get("research_snapshot_id")
  if not snapshot_id:
    raise ValueError("Research snapshot is required before content generation")

  run_id = callbacks["create_agent_run"](
    "content",
    {"platforms": state["platforms"], "research_snapshot_id": snapshot_id},
  )

  try:
    callbacks["log"](run_id, "content", "Starting content generation")

    research_summary = callbacks["get_research_summary"](snapshot_id)
    rag_query = f"{state['objective']} brand voice tone messaging"
    chunks = callbacks["retrieve_brand_context"](
      state["knowledge_base_id"],
      rag_query,
      settings["retrieve_default_k"],
    )
    brand_context = "\n\n".join(
      f"[score={chunk.get('score', 0):.2f}] {chunk['content']}" for chunk in chunks
    )

    callbacks["log"](
      run_id,
      "content",
      f"Retrieved {len(chunks)} brand voice chunks for grounding",
    )

    llm = ChatGoogleGenerativeAI(
      model=settings["chat_model"],
      google_api_key=settings["google_api_key"],
      temperature=0.7,
    )

    variant_labels = [chr(ord("A") + i) for i in range(max(1, ab_variants))]
    content_ids: list[str] = []

    for platform in state["platforms"]:
      if platform not in _PLATFORM_PROMPTS:
        continue

      for variant in variant_labels:
        callbacks["log"](run_id, "content", f"Generating {platform} variant {variant}")
        prompt = f"""{_PLATFORM_PROMPTS[platform]}{_VARIANT_SUFFIX.get(variant, "")}

Campaign objective: {state['objective']}
Target audience: {state.get('target_audience') or 'Not specified'}

Research summary:
{research_summary}

Brand voice guidelines (from knowledge base):
{brand_context or 'No brand context available.'}
"""
        response = llm.invoke(prompt)
        text = response.content if isinstance(response.content, str) else str(response.content)
        text = text.strip()

        title = None
        body = text
        if platform == "email" and text.lower().startswith("subject:"):
          lines = text.split("\n", 2)
          title = lines[0].replace("Subject:", "", 1).strip()
          body = lines[2].strip() if len(lines) > 2 else lines[-1].strip()
        elif platform == "blog" and text.startswith("#"):
          lines = text.split("\n", 1)
          title = lines[0].lstrip("# ").strip()
          body = lines[1].strip() if len(lines) > 1 else text

        content_id = callbacks["create_content"](platform, title, body, variant)
        content_ids.append(content_id)
        callbacks["log"](run_id, "content", f"Created {platform} variant {variant} draft")

    if not content_ids:
      raise ValueError("No supported platforms produced content")

    callbacks["complete_agent_run"](run_id, {"content_ids": content_ids})
    callbacks["log"](run_id, "content", "Content generation complete")
    callbacks["transition_campaign_status"]("generating", "approval_pending")

    return {"content_ids": content_ids}
  except Exception as exc:
    logger.exception("Content node failed")
    callbacks["fail_agent_run"](run_id, {"error": str(exc)})
    callbacks["log"](run_id, "content", f"Content generation failed: {exc}", "error")
    raise
