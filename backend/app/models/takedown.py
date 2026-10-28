import enum
import uuid
from sqlalchemy import String, Enum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TakedownStatus(str, enum.Enum):
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    ACTIONED = "actioned"
    REJECTED = "rejected"


class Takedown(Base, TimestampMixin):
    __tablename__ = "takedowns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    requester_name: Mapped[str] = mapped_column(String(200), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TakedownStatus] = mapped_column(Enum(TakedownStatus, values_callable=lambda enum_cls: [member.value for member in enum_cls]), default=TakedownStatus.RECEIVED)
    actioned_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    admin_notes: Mapped[str | None] = mapped_column(Text)