"""add quizzes category

Revision ID: 20260405_0007
Revises: 20260404_0006
Create Date: 2026-04-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260405_0007"
down_revision = "20260404_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("quizzes", sa.Column("category", sa.String(length=80), nullable=True))


def downgrade():
    op.drop_column("quizzes", "category")
