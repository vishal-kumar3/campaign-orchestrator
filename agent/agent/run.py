import logging

from agent.graph import get_compiled_graph
from agent.state import CampaignGraphState, GraphConfigurable

logger = logging.getLogger(__name__)


async def run_campaign_graph(
  *,
  initial_state: CampaignGraphState,
  graph_config: GraphConfigurable,
) -> CampaignGraphState:
  graph = get_compiled_graph()
  config = {
    "configurable": {
      **graph_config,
      "thread_id": initial_state["thread_id"],
    }
  }
  result = await graph.ainvoke(initial_state, config)
  return result


async def resume_campaign_graph(
  *,
  thread_id: str,
  graph_config: GraphConfigurable,
) -> CampaignGraphState:
  graph = get_compiled_graph()
  config = {
    "configurable": {
      **graph_config,
      "thread_id": thread_id,
    }
  }
  result = await graph.ainvoke(None, config)
  return result
