"""add para to attendance records

Revision ID: f1a2b3c4d5e6
Revises: c4a8d2e7f1ab
Create Date: 2026-04-21 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "c4a8d2e7f1ab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "attendance_records",
        sa.Column("para", sa.SmallInteger(), nullable=False, server_default="1"),
    )
    op.drop_constraint("uq_attendance_lesson_student", "attendance_records", type_="unique")
    op.create_unique_constraint(
        "uq_attendance_lesson_student_para",
        "attendance_records",
        ["lesson_id", "student_id", "para"],
    )
    op.alter_column("attendance_records", "para", server_default=None)


def downgrade() -> None:
    op.drop_constraint("uq_attendance_lesson_student_para", "attendance_records", type_="unique")
    op.create_unique_constraint(
        "uq_attendance_lesson_student",
        "attendance_records",
        ["lesson_id", "student_id"],
    )
    op.drop_column("attendance_records", "para")
