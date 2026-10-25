"""Add explicit public-display consent for contributed text.

Revision ID: 0003_text_public_consent
Revises: 0002_text_records
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_text_public_consent"
down_revision = "0002_text_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "text_records",
        sa.Column("allow_public_display", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("text_records", "allow_public_display")
