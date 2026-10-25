import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.media import MediaKind


class MediaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    speaker: str | None = Field(default=None, max_length=200)
    dialect: str | None = Field(default=None, max_length=100)
    county: str | None = Field(default=None, max_length=100)
    genre: str | None = Field(default=None, max_length=100)
    license: str = Field(min_length=1, max_length=100)
    consent_to_archive: bool = False
    confirm_rights: bool = False
    consent_to_publish: bool = False
    allow_research_use: bool = False
    allow_ai_training: bool = False
    allow_commercial_use: bool = False
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("title", "license")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


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
    allow_public_display: bool
    allow_research_use: bool
    allow_ai_training: bool
    allow_commercial_use: bool
    lang_score: float | None
    created_at: datetime


class MediaDetail(MediaRead):
    file_url: str
    sha256: str
    size_bytes: int | None


class MediaSubmissionDetail(MediaDetail):
    review_status: str = "pending"
    message: str = "Received for review. It will not be publicly listed until approved."
