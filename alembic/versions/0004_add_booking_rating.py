"""add booking rating

Revision ID: 0004_add_booking_rating
Revises: 0003_add_user_specialty
Create Date: 2026-04-28 13:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_booking_rating"
down_revision: str | None = "0003_add_user_specialty"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("rating", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "rating")
