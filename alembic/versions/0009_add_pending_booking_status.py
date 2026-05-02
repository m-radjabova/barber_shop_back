"""add pending booking status

Revision ID: 0009_add_pending_booking_status
Revises: 0008_add_telegram_link_fields
Create Date: 2026-05-02 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_add_pending_booking_status"
down_revision: str | None = "0008_add_telegram_link_fields"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'pending' BEFORE 'confirmed'")


def downgrade() -> None:
    pass
