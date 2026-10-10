"""initial schema

Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("contributor", "researcher", "reviewer", "admin", name="userrole"), nullable=False),
        sa.Column("institution", sa.String(200)),
        sa.Column("dialect", sa.String(100)),
        sa.Column("county", sa.String(100)),
        sa.Column("bio", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.Text, unique=True, nullable=False),
        sa.Column("domain", sa.String(255), nullable=False, index=True),
        sa.Column("source_type", sa.Enum("web", "youtube", "audio", "pdf", "book", "social", "user_upload", name="sourcetype"), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "taken_down", name="sourcestatus"), default="pending"),
        sa.Column("license", sa.String(100)),
        sa.Column("language_confidence", sa.Float),
        sa.Column("raw_metadata", sa.Text),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sources_url", "sources", ["url"])

    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), index=True),
        sa.Column("kind", sa.Enum("audio", "video", "image", name="mediakind"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("speaker", sa.String(200)),
        sa.Column("dialect", sa.String(100), index=True),
        sa.Column("county", sa.String(100)),
        sa.Column("genre", sa.String(100), index=True),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("sha256", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("lang_score", sa.Float),
        sa.Column("license", sa.String(100)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("media.id", ondelete="CASCADE"), index=True),
        sa.Column("start_seconds", sa.Float, nullable=False),
        sa.Column("end_seconds", sa.Float, nullable=False),
        sa.Column("transcript", sa.Text),
        sa.Column("translation", sa.Text),
        sa.Column("speaker_label", sa.String(100)),
        sa.Column("is_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("segments.id", ondelete="CASCADE"), index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), index=True),
        sa.Column("annotation_type", sa.Enum("pos", "lemma", "morphology", "tone", "ipa", "dialect", "translation", "transcription", "quality", name="annotationtype"), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contributor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), index=True),
        sa.Column("submission_type", sa.Enum("audio", "text", "video", "pdf", name="submissiontype"), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "needs_review", name="submissionstatus"), default="pending"),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("reviewer_notes", sa.Text),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "takedowns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.Text, nullable=False, index=True),
        sa.Column("requester_name", sa.String(200), nullable=False),
        sa.Column("requester_email", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("status", sa.Enum("received", "under_review", "actioned", "rejected", name="takedownstatus"), default="received"),
        sa.Column("actioned_at", sa.DateTime(timezone=True)),
        sa.Column("admin_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in ("takedowns", "submissions", "annotations", "segments", "media", "sources", "users"):
        op.drop_table(table)