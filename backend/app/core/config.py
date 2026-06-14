from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    populate_by_name=True,
  )

  database_url: str
  clerk_secret_key: str

  upload_dir: str = "./data/uploads"
  max_upload_bytes: int = 20 * 1024 * 1024

  google_api_key: str = ""
  embedding_model: str = Field(
    default="gemini-embedding-001",
    validation_alias="GEMINI_EMBEDDING_MODEL",
  )
  embedding_dimensions: int = Field(
    default=1536,
    validation_alias="GEMINI_EMBEDDING_DIMENSIONS",
  )
  chat_model: str = Field(
    default="gemini-2.0-flash",
    validation_alias="GEMINI_CHAT_MODEL",
  )

  chunk_size_tokens: int = 500
  chunk_overlap_tokens: int = 50
  retrieve_default_k: int = 3

  def ensure_upload_dir(self) -> Path:
    path = Path(self.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


settings = Settings()
