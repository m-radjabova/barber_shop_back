"""add lesson progress table

Revision ID: c3f4b76fd2a1
Revises: 8265a12f8925
Create Date: 2026-02-09 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3f4b76fd2a1"
down_revision: Union[str, None] = "8265a12f8925"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("last_position_sec", sa.Integer(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
    )
    op.create_index(op.f("ix_lesson_progress_id"), "lesson_progress", ["id"], unique=False)
    op.create_index(op.f("ix_lesson_progress_user_id"), "lesson_progress", ["user_id"], unique=False)
    op.create_index(op.f("ix_lesson_progress_course_id"), "lesson_progress", ["course_id"], unique=False)
    op.create_index(op.f("ix_lesson_progress_lesson_id"), "lesson_progress", ["lesson_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lesson_progress_lesson_id"), table_name="lesson_progress")
    op.drop_index(op.f("ix_lesson_progress_course_id"), table_name="lesson_progress")
    op.drop_index(op.f("ix_lesson_progress_user_id"), table_name="lesson_progress")
    op.drop_index(op.f("ix_lesson_progress_id"), table_name="lesson_progress")
    op.drop_table("lesson_progress")
