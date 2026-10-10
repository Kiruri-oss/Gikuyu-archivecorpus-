import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.source import SourceType, SourceStatus


class SourceCreate(BaseModel):
    url: str
    source_type: SourceType
    license: str | None = None
    raw_metadata: str | None = None


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