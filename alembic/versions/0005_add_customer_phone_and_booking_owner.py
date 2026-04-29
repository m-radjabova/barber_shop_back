"""add customer phone and booking owner

Revision ID: 0005_customer_booking_owner
Revises: 0004_add_booking_rating
Create Date: 2026-04-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_customer_booking_owner"
down_revision: str | None = "0004_add_booking_rating"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=True)

    op.add_column("bookings", sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_bookings_customer_id"), "bookings", ["customer_id"], unique=False)
    op.create_foreign_key(
        "fk_bookings_customer_id_users",
        "bookings",
        "users",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_bookings_customer_id_users", "bookings", type_="foreignkey")
    op.drop_index(op.f("ix_bookings_customer_id"), table_name="bookings")
    op.drop_column("bookings", "customer_id")

    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_column("users", "phone_number")
