import uuid
from sqlalchemy import String, Text, ForeignKey, BigInteger, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TextRecord(Base, TimestampMixin):
    __tablename__ = "text_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    contributor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="ki")
    dialect: Mapped[str | None] = mapped_column(String(100), index=True)
    genre: Mapped[str | None] = mapped_column(String(100), index=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    lang_score: Mapped[float | None] = mapped_column(Float)
    license: Mapped[str] = mapped_column(String(100), nullable=False)
    allow_public_display: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_research_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_ai_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_commercial_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    source = relationship("Source", back_populates="texts")
    contributor = relationship("User")
