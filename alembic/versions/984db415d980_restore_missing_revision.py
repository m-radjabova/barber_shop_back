"""restore missing revision

Revision ID: 984db415d980
Revises: a0ada980e5bd
Create Date: 2026-02-09
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "984db415d980"
down_revision = "a0ada980e5bd"
branch_labels = None
depends_on = None


def upgrade():
    # Placeholder revision file (was missing)
    pass


def downgrade():
    pass
