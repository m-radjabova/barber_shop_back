"""add user specialty

Revision ID: 0003_add_user_specialty
Revises: 0002_add_bookings
Create Date: 2026-04-28 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_user_specialty"
down_revision: str | None = "0002_add_bookings"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("specialty", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "specialty")
