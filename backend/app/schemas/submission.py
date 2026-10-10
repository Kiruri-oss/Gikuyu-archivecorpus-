import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.submission import SubmissionType, SubmissionStatus


class SubmissionCreate(BaseModel):
    submission_type: SubmissionType
    title: str = Field(min_length=1, max_length=500)
    payload: str = Field(min_length=1)


class SubmissionReview(BaseModel):
    status: SubmissionStatus
    reviewer_notes: str | None = None


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contributor_id: uuid.UUID
    submission_type: SubmissionType
    status: SubmissionStatus
    title: str
    payload: str
    reviewer_notes: str | None = None
    reviewer_id: uuid.UUID | None = None
    created_at: datetime