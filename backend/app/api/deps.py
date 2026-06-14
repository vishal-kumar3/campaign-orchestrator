from collections.abc import Generator

from clerk_backend_api import Clerk
from core.config import Settings
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

security = HTTPBearer()
clerk = Clerk(bearer_auth=Settings.clerk_secret_key)


def get_db() -> Generator[Session, None, None]:
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
):
  token = credentials.credentials

  try:
    claims = clerk.verify_token(token)
    return claims
  except Exception:
    raise HTTPException(status_code=401, detail="Invalid token")
