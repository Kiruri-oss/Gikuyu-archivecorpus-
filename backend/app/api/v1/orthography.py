from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.orthography import suggest_orthography

router = APIRouter(prefix="/orthography", tags=["orthography"])


class OrthographyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class OrthographyChange(BaseModel):
    original: str
    suggested: str
    start: int
    end: int


class OrthographyResponse(BaseModel):
    original_text: str
    suggested_text: str
    suggestions: list[OrthographyChange]
    note: str = "Suggestions are not automatically saved. Confirm them with a fluent speaker before publishing."


@router.post("/suggest", response_model=OrthographyResponse)
async def orthography_suggestions(payload: OrthographyRequest) -> OrthographyResponse:
    proposed, suggestions = suggest_orthography(payload.text)
    return OrthographyResponse(
        original_text=payload.text,
        suggested_text=proposed,
        suggestions=[OrthographyChange(**item.__dict__) for item in suggestions],
    )
