import uuid
from pydantic import BaseModel, Field, ConfigDict


class SegmentCreate(BaseModel):
    media_id: uuid.UUID
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    transcript: str | None = None
    translation: str | None = None
    speaker_label: str | None = None


class SegmentUpdate(BaseModel):
    transcript: str | None = None
    translation: str | None = None


class SegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    media_id: uuid.UUID
    start_seconds: float
    end_seconds: float
    transcript: str | None
    translation: str | None
    is_verified: bool
    confidence: float | None