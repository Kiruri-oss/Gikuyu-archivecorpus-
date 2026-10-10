import enum
import uuid
from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SubmissionType(str, enum.Enum):
    AUDIO = "audio"
    TEXT = "text"
    VIDEO = "video"
    PDF = "pdf"


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contributor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    submission_type: Mapped[SubmissionType] = mapped_column(Enum(SubmissionType), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))