from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx


@dataclass
class RetrievedChunk:
  chunk_id: str
  document_id: str
  chunk_index: int
  content: str
  score: float
  metadata: dict[str, Any] | None


class RagClient:
  def __init__(
    self,
    base_url: str,
    get_token: Callable[[], str | Awaitable[str | None]],
  ) -> None:
    self._base_url = base_url.rstrip("/")
    self._get_token = get_token

  async def _auth_headers(self) -> dict[str, str]:
    token = self._get_token()
    if hasattr(token, "__await__"):
      token = await token
    if not token:
      raise RuntimeError("No auth token available for RAG retrieval")
    return {"Authorization": f"Bearer {token}"}

  async def retrieve(
    self,
    workspace_id: str,
    knowledge_base_id: str,
    query: str,
    *,
    k: int = 3,
  ) -> list[RetrievedChunk]:
    path = (
      f"{self._base_url}/workspaces/{workspace_id}/knowledge-bases/"
      f"{knowledge_base_id}/retrieve?q={quote(query)}&k={k}"
    )
    headers = await self._auth_headers()
    async with httpx.AsyncClient() as client:
      response = await client.get(path, headers=headers, timeout=30.0)
      response.raise_for_status()
      payload = response.json()

    return [
      RetrievedChunk(
        chunk_id=item["chunk_id"],
        document_id=item["document_id"],
        chunk_index=item["chunk_index"],
        content=item["content"],
        score=item["score"],
        metadata=item.get("metadata"),
      )
      for item in payload.get("chunks", [])
    ]
