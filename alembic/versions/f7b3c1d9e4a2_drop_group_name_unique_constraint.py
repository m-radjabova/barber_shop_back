"""drop group name unique constraint within course

Revision ID: f7b3c1d9e4a2
Revises: 32ad5a9573d8
Create Date: 2026-04-20 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f7b3c1d9e4a2"
down_revision = "32ad5a9573d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_groups_course_name", "groups", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_groups_course_name",
        "groups",
        ["course_id", "name"],
    )
