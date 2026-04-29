"""add barber profile fields

Revision ID: 0006_add_barber_profile_fields
Revises: 0005_customer_booking_owner
Create Date: 2026-04-29 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0006_add_barber_profile_fields"
down_revision: str | None = "0005_customer_booking_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("bio", sa.String(length=1200), nullable=True))
    op.add_column("users", sa.Column("location_text", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("work_start_time", sa.Time(), nullable=True))
    op.add_column("users", sa.Column("work_end_time", sa.Time(), nullable=True))
    op.add_column("users", sa.Column("services", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "services")
    op.drop_column("users", "work_end_time")
    op.drop_column("users", "work_start_time")
    op.drop_column("users", "location_text")
    op.drop_column("users", "bio")
