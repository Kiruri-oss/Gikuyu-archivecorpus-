"""Add explicit language scope to archived media.

Revision ID: 0005_media_language_code
Revises: 0004_media_permissions
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_media_language_code"
down_revision = "0004_media_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "media",
        sa.Column("language_code", sa.String(length=10), nullable=False, server_default="ki"),
    )
    op.create_index("ix_media_language_code", "media", ["language_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_media_language_code", table_name="media")
    op.drop_column("media", "language_code")
