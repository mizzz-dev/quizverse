"""add users password_hash column

Revision ID: 20260404_0005
Revises: 20260401_0003
Create Date: 2026-04-04 00:55:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0005"
down_revision = "20260401_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("users", "password_hash")
