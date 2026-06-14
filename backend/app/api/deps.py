import uuid
from collections.abc import Generator
from typing import Any

from clerk_backend_api.security import (
    TokenVerificationError,
    VerifyTokenOptions,
    verify_token_async,
)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.workspace import Workspace
from app.db.queries import workspace as workspace_queries
from app.db.session import SessionLocal

security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    try:
        return await verify_token_async(
            credentials.credentials,
            VerifyTokenOptions(secret_key=settings.clerk_secret_key),
        )
    except TokenVerificationError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    sub = user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    return sub


def get_owned_workspace(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> Workspace:
    workspace = workspace_queries.get_by_id_for_owner(db, workspace_id, user_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace
