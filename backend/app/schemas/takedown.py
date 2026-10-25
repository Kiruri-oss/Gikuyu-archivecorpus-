import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.takedown import TakedownStatus


class TakedownCreate(BaseModel):
    url: str = Field(min_length=5, max_length=2000)
    requester_name: str = Field(min_length=2, max_length=200)
    requester_email: EmailStr
    reason: str = Field(min_length=10, max_length=5000)


class TakedownRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    url: str
    requester_name: str
    requester_email: EmailStr
    reason: str
    status: TakedownStatus
    created_at: datetime
    actioned_at: datetime | None
    admin_notes: str | None = None