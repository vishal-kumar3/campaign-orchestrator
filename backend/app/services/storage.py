import re
import uuid
from pathlib import Path
from typing import Protocol

from app.core.config import settings


def _sanitize_filename(file_name: str) -> str:
  name = Path(file_name).name
  name = re.sub(r"[^\w.\-]", "_", name)
  return name or "document.pdf"


class StorageBackend(Protocol):
  def build_key(
    self,
    workspace_id: uuid.UUID,
    kb_id: uuid.UUID,
    document_id: uuid.UUID,
    file_name: str,
  ) -> str: ...

  def save(self, key: str, data: bytes) -> str: ...

  def read(self, key: str) -> bytes: ...

  def delete(self, key: str) -> None: ...


class LocalStorageBackend:
  def __init__(self, base_dir: Path) -> None:
    self._base_dir = base_dir.resolve()

  def build_key(
    self,
    workspace_id: uuid.UUID,
    kb_id: uuid.UUID,
    document_id: uuid.UUID,
    file_name: str,
  ) -> str:
    safe_name = _sanitize_filename(file_name)
    return (
      f"workspaces/{workspace_id}/knowledge-bases/{kb_id}/"
      f"documents/{document_id}/{safe_name}"
    )

  def _resolve(self, key: str) -> Path:
    normalized = key.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
      raise ValueError("Invalid storage key")
    path = (self._base_dir / normalized).resolve()
    if not str(path).startswith(str(self._base_dir)):
      raise ValueError("Invalid storage key")
    return path

  def save(self, key: str, data: bytes) -> str:
    path = self._resolve(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key

  def read(self, key: str) -> bytes:
    return self._resolve(key).read_bytes()

  def delete(self, key: str) -> None:
    path = self._resolve(key)
    if path.exists():
      path.unlink()


def get_storage() -> StorageBackend:
  base_dir = settings.ensure_upload_dir()
  return LocalStorageBackend(base_dir)
