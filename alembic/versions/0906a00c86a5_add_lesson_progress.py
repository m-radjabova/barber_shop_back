"""add lesson_progress

Revision ID: 0906a00c86a5
Revises: a0ada980e5bd
Create Date: 2026-02-08 17:08:28.464419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0906a00c86a5'
down_revision: Union[str, None] = 'a0ada980e5bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass