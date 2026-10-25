from typing import Literal
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, PlainTextResponse

from app.core.deps import DbSession, ResearcherUser
from app.services.export import export_service

router = APIRouter(prefix="/exports", tags=["exports"])
LicenseFilter = Literal["all", "CC0", "CC-BY", "PUBLIC-DOMAIN"]


@router.get("/jsonl")
async def export_jsonl(
    db: DbSession,
    _: ResearcherUser,
    dialect: str | None = None,
    purpose: Literal["research", "ai_training", "commercial"] = Query(default="research"),
    license_filter: LicenseFilter = Query(default="all"),
) -> StreamingResponse:
    async def stream():
        async for line in export_service.export_jsonl(
            db, dialect, purpose, None if license_filter == "all" else license_filter
        ):
            yield line
    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="gikuyu-archive-{purpose}.jsonl"'},
    )


@router.get("/csv")
async def export_csv(
    db: DbSession,
    _: ResearcherUser,
    dialect: str | None = None,
    purpose: Literal["research", "ai_training", "commercial"] = Query(default="research"),
    license_filter: LicenseFilter = Query(default="all"),
) -> PlainTextResponse:
    csv_data = await export_service.export_csv(
        db, dialect, purpose, None if license_filter == "all" else license_filter
    )
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="gikuyu-archive-{purpose}.csv"'},
    )
