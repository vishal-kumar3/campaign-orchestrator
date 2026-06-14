from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
  items: list[T]
  total: int


class PaginationParams(BaseModel):
  limit: int = Field(default=50, ge=1, le=100)
  offset: int = Field(default=0, ge=0)
