"""add blocked booking status

Revision ID: 0010_add_blocked_booking_status
Revises: 0009_add_pending_booking_status
Create Date: 2026-05-05 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_add_blocked_booking_status"
down_revision: str | None = "0009_add_pending_booking_status"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'blocked' AFTER 'confirmed'")


def downgrade() -> None:
    pass
