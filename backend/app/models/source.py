import enum
import uuid
from sqlalchemy import String, Enum, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SourceType(str, enum.Enum):
    WEB = "web"
    YOUTUBE = "youtube"
    AUDIO = "audio"
    PDF = "pdf"
    BOOK = "book"
    SOCIAL = "social"
    USER_UPLOAD = "user_upload"


class SourceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TAKEN_DOWN = "taken_down"


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus), default=SourceStatus.PENDING, nullable=False)
    license: Mapped[str | None] = mapped_column(String(100))
    language_confidence: Mapped[float | None] = mapped_column(Float)
    raw_metadata: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    media = relationship("Media", back_populates="source", cascade="all, delete-orphan")
    texts = relationship("TextRecord", back_populates="source", cascade="all, delete-orphan")