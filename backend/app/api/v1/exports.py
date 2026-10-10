from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, PlainTextResponse

from app.core.deps import DbSession
from app.services.export import export_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/jsonl")
async def export_jsonl(db: DbSession, dialect: str | None = None) -> StreamingResponse:
    async def stream():
        async for line in export_service.export_jsonl(db, dialect):
            yield line
    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.get("/csv")
async def export_csv(db: DbSession, dialect: str | None = None) -> PlainTextResponse:
    csv_data = await export_service.export_csv(db, dialect)
    return PlainTextResponse(csv_data, media_type="text/csv")