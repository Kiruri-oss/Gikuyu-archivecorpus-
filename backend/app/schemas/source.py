import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.source import SourceType, SourceStatus


class SourceCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
    source_type: SourceType
    license: str | None = Field(default=None, max_length=100)
    raw_metadata: str | None = Field(default=None, max_length=10000)


class SourceReview(BaseModel):
    status: SourceStatus
    reviewer_notes: str | None = Field(default=None, max_length=5000)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    domain: str
    source_type: SourceType
    status: SourceStatus
    license: str | None = None
    language_confidence: float | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewer_notes: str | None = None
