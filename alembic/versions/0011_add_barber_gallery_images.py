"""add barber gallery images

Revision ID: 0011_add_barber_gallery_images
Revises: 0010_add_blocked_booking_status
Create Date: 2026-05-05 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0011_add_barber_gallery_images"
down_revision: Union[str, None] = "0010_add_blocked_booking_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("gallery_images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "gallery_images")
