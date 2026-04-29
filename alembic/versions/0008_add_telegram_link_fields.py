"""add telegram link fields

Revision ID: 0008_add_telegram_link_fields
Revises: 0007_location_coords_promo
Create Date: 2026-04-29 23:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008_add_telegram_link_fields"
down_revision: str | None = "0007_location_coords_promo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "users",
        sa.Column("telegram_notifications_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("telegram_marketing_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("users", sa.Column("telegram_link_token", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("telegram_link_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("telegram_connected_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_users_telegram_chat_id"), "users", ["telegram_chat_id"], unique=True)
    op.create_index(op.f("ix_users_telegram_link_token"), "users", ["telegram_link_token"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_telegram_link_token"), table_name="users")
    op.drop_index(op.f("ix_users_telegram_chat_id"), table_name="users")
    op.drop_column("users", "telegram_connected_at")
    op.drop_column("users", "telegram_link_expires_at")
    op.drop_column("users", "telegram_link_token")
    op.drop_column("users", "telegram_marketing_enabled")
    op.drop_column("users", "telegram_notifications_enabled")
    op.drop_column("users", "telegram_chat_id")
