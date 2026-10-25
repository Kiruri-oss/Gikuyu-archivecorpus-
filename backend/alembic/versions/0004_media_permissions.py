"""Add explicit rights and publication flags for uploaded media.

Revision ID: 0004_media_permissions
Revises: 0003_text_public_consent
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_media_permissions"
down_revision = "0003_text_public_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("media", sa.Column("allow_public_display", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("media", sa.Column("allow_research_use", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("media", sa.Column("allow_ai_training", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("media", sa.Column("allow_commercial_use", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("media", "allow_commercial_use")
    op.drop_column("media", "allow_ai_training")
    op.drop_column("media", "allow_research_use")
    op.drop_column("media", "allow_public_display")
