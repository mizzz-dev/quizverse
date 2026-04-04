"""extend otp_verifications for destination-based verification

Revision ID: 20260404_0006
Revises: 20260404_0005
Create Date: 2026-04-04 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0006"
down_revision = "20260404_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("otp_verifications", sa.Column("destination", sa.String(length=255), nullable=True))
    op.execute("UPDATE otp_verifications SET destination = '' WHERE destination IS NULL")
    op.alter_column("otp_verifications", "destination", nullable=False)
    op.alter_column("otp_verifications", "user_id", nullable=True)
    op.create_index(
        "ix_otp_verifications_destination_channel_purpose",
        "otp_verifications",
        ["destination", "channel", "purpose"],
    )


def downgrade():
    op.drop_index("ix_otp_verifications_destination_channel_purpose", table_name="otp_verifications")
    op.alter_column("otp_verifications", "user_id", nullable=False)
    op.drop_column("otp_verifications", "destination")
