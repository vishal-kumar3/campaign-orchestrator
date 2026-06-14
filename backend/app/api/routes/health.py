from fastapi import APIRouter

from app.schemas.health import HealthGetResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthGetResponse)
def health_check() -> HealthGetResponse:
  return HealthGetResponse(message="Hello World")
