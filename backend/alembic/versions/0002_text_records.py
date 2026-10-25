"""Add reviewed source state and persistent text records.

Revision ID: 0002_text_records
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_text_records"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("sources", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sources", sa.Column("reviewer_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_sources_reviewed_by_users", "sources", "users",
        ["reviewed_by"], ["id"], ondelete="SET NULL"
    )

    op.create_table(
        "text_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contributor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language_code", sa.String(16), nullable=False, server_default="ki"),
        sa.Column("dialect", sa.String(100), nullable=True),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("lang_score", sa.Float(), nullable=True),
        sa.Column("license", sa.String(100), nullable=False),
        sa.Column("allow_research_use", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_ai_training", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_commercial_use", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_text_records_source_id", "text_records", ["source_id"])
    op.create_index("ix_text_records_contributor_id", "text_records", ["contributor_id"])
    op.create_index("ix_text_records_language_code", "text_records", ["language_code"])
    op.create_index("ix_text_records_dialect", "text_records", ["dialect"])
    op.create_index("ix_text_records_genre", "text_records", ["genre"])
    op.create_index("ix_text_records_sha256", "text_records", ["sha256"], unique=True)


def downgrade() -> None:
    op.drop_table("text_records")
    op.drop_constraint("fk_sources_reviewed_by_users", "sources", type_="foreignkey")
    op.drop_column("sources", "reviewer_notes")
    op.drop_column("sources", "reviewed_at")
    op.drop_column("sources", "reviewed_by")
