"""Create account-scoped saved references.

Revision ID: 0006_saved_references
Revises: 0005_media_language_code
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_saved_references"
down_revision = "0005_media_language_code"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_key", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "reference_key", name="uq_saved_references_user_key"),
    )
    op.create_index("ix_saved_references_user_id", "saved_references", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_saved_references_user_id", table_name="saved_references")
    op.drop_table("saved_references")
