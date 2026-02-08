"""add lesson_progress

Revision ID: 984db415d980
Revises: 0906a00c86a5
Create Date: 2026-02-08 17:09:09.268015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '984db415d980'
down_revision: Union[str, None] = '0906a00c86a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass