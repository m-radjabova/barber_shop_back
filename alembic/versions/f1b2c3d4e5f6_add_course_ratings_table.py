"""add course ratings table

Revision ID: f1b2c3d4e5f6
Revises: d98f0b8e9d21
Create Date: 2026-02-14 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, None] = "d98f0b8e9d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_ratings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "user_id", name="uq_course_rating_course_user"),
    )
    op.create_index(op.f("ix_course_ratings_id"), "course_ratings", ["id"], unique=False)
    op.create_index(op.f("ix_course_ratings_course_id"), "course_ratings", ["course_id"], unique=False)
    op.create_index(op.f("ix_course_ratings_user_id"), "course_ratings", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_course_ratings_user_id"), table_name="course_ratings")
    op.drop_index(op.f("ix_course_ratings_course_id"), table_name="course_ratings")
    op.drop_index(op.f("ix_course_ratings_id"), table_name="course_ratings")
    op.drop_table("course_ratings")
