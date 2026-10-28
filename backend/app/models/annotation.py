import enum
import uuid
from sqlalchemy import String, Enum, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AnnotationType(str, enum.Enum):
    POS = "pos"
    LEMMA = "lemma"
    MORPHOLOGY = "morphology"
    TONE = "tone"
    IPA = "ipa"
    DIALECT = "dialect"
    TRANSLATION = "translation"
    TRANSCRIPTION = "transcription"
    QUALITY = "quality"


class Annotation(Base, TimestampMixin):
    __tablename__ = "annotations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("segments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    annotation_type: Mapped[AnnotationType] = mapped_column(Enum(AnnotationType, values_callable=lambda enum_cls: [member.value for member in enum_cls]), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    segment = relationship("Segment", back_populates="annotations")