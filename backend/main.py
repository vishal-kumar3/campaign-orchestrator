from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.graph import setup_checkpointer
from app.api.routes import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
  try:
    setup_checkpointer(settings.database_url)
  except Exception as exc:
    import logging

    logging.getLogger(__name__).warning("Checkpointer setup skipped: %s", exc)
  yield


app = FastAPI(
  title="AI Campaign Manager",
  description="AI Campaign Manager is a platform for creating and managing AI-powered campaigns.",
  version="0.1.0",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
