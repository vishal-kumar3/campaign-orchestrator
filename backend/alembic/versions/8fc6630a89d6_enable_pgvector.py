"""enable pgvector

Revision ID: 8fc6630a89d6
Revises: a5ac5260fc5f
Create Date: 2026-06-07 21:57:08.025934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fc6630a89d6'
down_revision: Union[str, Sequence[str], None] = 'a5ac5260fc5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
  op.execute("DROP EXTENSION IF EXISTS vector")
