from langchain_core.runnables import RunnableConfig

from agent.state import GraphConfigurable


def get_graph_config(config: RunnableConfig) -> GraphConfigurable:
  return config["configurable"]  # type: ignore[return-value]


def get_callbacks(config: RunnableConfig):
  return get_graph_config(config)["callbacks"]


def get_settings(config: RunnableConfig):
  return get_graph_config(config)["settings"]
