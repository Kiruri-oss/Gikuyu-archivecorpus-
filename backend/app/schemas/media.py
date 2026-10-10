import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.media import MediaKind


class MediaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    speaker: str | None = None
    dialect: str | None = None
    county: str | None = None
    genre: str | None = None
    license: str | None = None
    notes: str | None = None


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    kind: MediaKind
    title: str
    speaker: str | None
    dialect: str | None
    county: str | None
    genre: str | None
    duration_seconds: float | None
    license: str | None
    lang_score: float | None
    created_at: datetime


class MediaDetail(MediaRead):
    file_url: str
    sha256: str
    size_bytes: int | None