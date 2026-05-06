"""add barber applications

Revision ID: 0012_add_barber_applications
Revises: 0011_add_barber_gallery_images
Create Date: 2026-05-06 11:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0012_add_barber_applications"
down_revision: str | None = "0011_add_barber_gallery_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    barber_application_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="barber_application_status",
    )
    barber_application_status.create(op.get_bind(), checkfirst=True)
    barber_application_status_no_create = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="barber_application_status",
        create_type=False,
    )

    op.create_table(
        "barber_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("location_text", sa.String(length=255), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("passport_series", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("payment_card_number", sa.String(length=32), nullable=False),
        sa.Column("payment_amount", sa.Integer(), nullable=False),
        sa.Column("payment_note", sa.Text(), nullable=False),
        sa.Column("receipt_file_url", sa.String(length=500), nullable=False),
        sa.Column(
            "status",
            barber_application_status_no_create,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_barber_applications_user_id"), "barber_applications", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_barber_applications_user_id"), table_name="barber_applications")
    op.drop_table("barber_applications")
    postgresql.ENUM(name="barber_application_status").drop(op.get_bind(), checkfirst=True)
