

from fastapi import FastAPI

from app.api.routes import api_router

app = FastAPI(
  title="AI Campaign Manager",
  description="AI Campaign Manager is a platform for creating and managing AI-powered campaigns.",
  version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
