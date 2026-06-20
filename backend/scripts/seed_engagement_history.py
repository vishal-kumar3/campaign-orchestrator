"""Seed engagement_history with synthetic data for scheduler demos."""

import sys
import uuid

from sqlalchemy import select

from app.db.models.workspace import Workspace
from app.db.queries import engagement_history as engagement_history_queries
from app.db.session import SessionLocal


def main() -> None:
  workspace_id = uuid.UUID(sys.argv[1]) if len(sys.argv) > 1 else None
  db = SessionLocal()
  try:
    if workspace_id:
      count = engagement_history_queries.seed_for_workspace(db, workspace_id)
      print(f"Seeded {count} rows for workspace {workspace_id}")
      return

    workspaces = list(db.scalars(select(Workspace)).all())
    total = 0
    for ws in workspaces:
      total += engagement_history_queries.seed_for_workspace(db, ws.id)
    print(f"Seeded {total} rows across {len(workspaces)} workspaces")
  finally:
    db.close()


if __name__ == "__main__":
  main()
