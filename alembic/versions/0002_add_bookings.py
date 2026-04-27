"""add bookings table

Revision ID: 0002_add_bookings
Revises: 0001_initial_users
Create Date: 2026-04-27 00:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_add_bookings"
down_revision: str | None = "0001_initial_users"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

booking_status_enum = postgresql.ENUM(
    "confirmed",
    "completed",
    "cancelled",
    name="booking_status",
    create_type=False,
)


def upgrade() -> None:
    booking_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "bookings",
        sa.Column("booking_code", sa.String(length=12), nullable=False),
        sa.Column("barber_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_name", sa.String(length=120), nullable=False),
        sa.Column("client_phone", sa.String(length=32), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("appointment_time", sa.Time(), nullable=False),
        sa.Column("status", booking_status_enum, nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["barber_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_code"),
    )
    op.create_index(op.f("ix_bookings_appointment_date"), "bookings", ["appointment_date"], unique=False)
    op.create_index(op.f("ix_bookings_barber_id"), "bookings", ["barber_id"], unique=False)
    op.create_index(op.f("ix_bookings_booking_code"), "bookings", ["booking_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_booking_code"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_barber_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_appointment_date"), table_name="bookings")
    op.drop_table("bookings")
    booking_status_enum.drop(op.get_bind(), checkfirst=True)
