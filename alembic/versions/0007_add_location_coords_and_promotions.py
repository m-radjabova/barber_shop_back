"""add location coords and promotions

Revision ID: 0007_location_coords_promo
Revises: 0006_add_barber_profile_fields
Create Date: 2026-04-29 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007_location_coords_promo"
down_revision: str | None = "0006_add_barber_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("location_lat", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("location_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "location_lng")
    op.drop_column("users", "location_lat")
