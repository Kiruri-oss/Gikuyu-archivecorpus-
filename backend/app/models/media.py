import enum
import uuid
from sqlalchemy import String, Enum, Text, Float, ForeignKey, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MediaKind(str, enum.Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class Media(Base, TimestampMixin):
    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    kind: Mapped[MediaKind] = mapped_column(Enum(MediaKind), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="ki", server_default="ki", index=True)
    speaker: Mapped[str | None] = mapped_column(String(200))
    dialect: Mapped[str | None] = mapped_column(String(100), index=True)
    county: Mapped[str | None] = mapped_column(String(100))
    genre: Mapped[str | None] = mapped_column(String(100), index=True)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    lang_score: Mapped[float | None] = mapped_column(Float)
    license: Mapped[str | None] = mapped_column(String(100))
    allow_public_display: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_research_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_ai_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_commercial_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    source = relationship("Source", back_populates="media")
    segments = relationship("Segment", back_populates="media", cascade="all, delete-orphan")