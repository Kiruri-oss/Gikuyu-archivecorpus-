import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TextRecordCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=2_000_000)
    language_code: str = Field(default="ki", min_length=2, max_length=16, pattern=r"^[a-z]{2,3}(-[A-Za-z0-9]+)*$")
    author: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1000, le=2100)
    dialect: str | None = Field(default=None, max_length=100)
    genre: str | None = Field(default=None, max_length=100)
    license: str = Field(min_length=1, max_length=100)
    consent_to_publish: bool = False
    allow_research_use: bool = False
    allow_ai_training: bool = False
    allow_commercial_use: bool = False
    consent_to_archive: bool = False
    confirm_rights: bool = False
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("title", "body", "license")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class TextRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    author: str | None
    year: int | None
    body: str
    language_code: str
    dialect: str | None
    genre: str | None
    license: str
    allow_public_display: bool
    allow_research_use: bool
    allow_ai_training: bool
    allow_commercial_use: bool
    created_at: datetime

class TextRecordSubmissionRead(TextRecordRead):
    review_status: str = "pending"
    message: str = "Received for review. It is not public until a reviewer approves publication."
