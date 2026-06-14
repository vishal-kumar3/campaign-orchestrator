from google import genai
from google.genai import types

from app.core.config import settings

_client: genai.Client | None = None

_EMBED_BATCH_SIZE = 100


def get_gemini_client() -> genai.Client:
  global _client
  if _client is None:
    if not settings.google_api_key:
      raise RuntimeError("GOOGLE_API_KEY is not configured")
    _client = genai.Client(api_key=settings.google_api_key)
  return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
  if not texts:
    return []

  client = get_gemini_client()
  vectors: list[list[float]] = []

  for start in range(0, len(texts), _EMBED_BATCH_SIZE):
    batch = texts[start : start + _EMBED_BATCH_SIZE]
    result = client.models.embed_content(
      model=settings.embedding_model,
      contents=batch,
      config=types.EmbedContentConfig(
        output_dimensionality=settings.embedding_dimensions,
      ),
    )
    if not result.embeddings:
      raise ValueError("Gemini returned no embeddings")
    for embedding in result.embeddings:
      if embedding.values is None:
        raise ValueError("Gemini returned empty embedding values")
      vector = list(embedding.values)
      if len(vector) != settings.embedding_dimensions:
        raise ValueError(
          f"Expected {settings.embedding_dimensions} dims, got {len(vector)}"
        )
      vectors.append(vector)

  return vectors


def embed_query(text: str) -> list[float]:
  return embed_texts([text])[0]
