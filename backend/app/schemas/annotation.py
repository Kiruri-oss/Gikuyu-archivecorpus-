import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.annotation import AnnotationType


class AnnotationCreate(BaseModel):
    annotation_type: AnnotationType
    value: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None


class AnnotationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    segment_id: uuid.UUID
    user_id: uuid.UUID
    annotation_type: AnnotationType
    value: str
    confidence: float | None = None
    notes: str | None = None
    created_at: datetime