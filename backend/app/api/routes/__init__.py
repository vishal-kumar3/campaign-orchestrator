
from fastapi import APIRouter

from app.api.routes import (
  campaigns,
  contents,
  documents,
  health,
  knowledge_bases,
  workspaces,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(workspaces.router)
api_router.include_router(campaigns.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(documents.router)
api_router.include_router(contents.router)
