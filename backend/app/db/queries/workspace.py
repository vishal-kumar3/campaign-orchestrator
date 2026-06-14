import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.workspace import Workspace


def get_by_id_for_owner(
  session: Session, workspace_id: uuid.UUID, owner_id: str
) -> Workspace | None:
  return session.scalar(
    select(Workspace).where(
      Workspace.id == workspace_id,
      Workspace.owner_id == owner_id,
    )
  )


def list_for_owner(
  session: Session, owner_id: str, *, limit: int, offset: int
) -> tuple[list[Workspace], int]:
  base = select(Workspace).where(Workspace.owner_id == owner_id)
  total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
  items = list(
    session.scalars(
      base.order_by(Workspace.created_at.desc()).limit(limit).offset(offset)
    ).all()
  )
  return items, total


def create(
  session: Session, *, owner_id: str, name: str, description: str | None
) -> Workspace:
  workspace = Workspace(owner_id=owner_id, name=name, description=description)
  session.add(workspace)
  session.commit()
  session.refresh(workspace)
  return workspace


def update(session: Session, workspace: Workspace, **fields) -> Workspace:
  for key, value in fields.items():
    setattr(workspace, key, value)
  session.commit()
  session.refresh(workspace)
  return workspace


def delete(session: Session, workspace: Workspace) -> None:
  session.delete(workspace)
  session.commit()
