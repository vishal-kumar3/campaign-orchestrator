import logging
import os

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg_pool import ConnectionPool

from agent.nodes.content import content_node
from agent.nodes.publisher import publisher_node
from agent.nodes.research import research_node
from agent.state import CampaignGraphState

logger = logging.getLogger(__name__)

_checkpointer: PostgresSaver | None = None
_pool: ConnectionPool | None = None


def _normalize_db_url(url: str) -> str:
  return url.replace("postgresql+psycopg://", "postgresql://").replace(
    "postgresql+psycopg2://", "postgresql://"
  )


def setup_checkpointer(database_url: str | None = None) -> None:
  global _checkpointer, _pool, _compiled_graph
  if _checkpointer is not None:
    return

  raw_url = database_url or os.environ.get("DATABASE_URL", "")
  if not raw_url:
    logger.warning("DATABASE_URL not set; LangGraph checkpointer disabled")
    return

  dsn = _normalize_db_url(raw_url)

  def _configure(conn) -> None:
    conn.autocommit = True

  _pool = ConnectionPool(dsn, configure=_configure, max_size=5)
  _checkpointer = PostgresSaver(_pool)
  _checkpointer.setup()
  _compiled_graph = None
  logger.info("LangGraph PostgresSaver initialized")


_compiled_graph = None


def get_compiled_graph():
  global _compiled_graph
  if _compiled_graph is not None:
    return _compiled_graph

  builder = StateGraph(CampaignGraphState)
  builder.add_node("research", research_node)
  builder.add_node("content", content_node)
  builder.add_node("publisher", publisher_node)
  builder.add_edge(START, "research")
  builder.add_edge("research", "content")
  builder.add_edge("content", "publisher")
  builder.add_edge("publisher", END)

  if _checkpointer is not None:
    _compiled_graph = builder.compile(
      checkpointer=_checkpointer,
      interrupt_before=["publisher"],
    )
  else:
    logger.warning("Checkpointer disabled; human-in-the-loop publish will not work")
    _compiled_graph = builder.compile()
  return _compiled_graph


def is_checkpointer_enabled() -> bool:
  return _checkpointer is not None
