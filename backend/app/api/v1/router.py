from fastapi import APIRouter

from app.api.v1 import (
    auth,
    sources,
    media,
    segments,
    annotations,
    submissions,
    search,
    exports,
    takedowns,
    text_records,
    orthography,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(sources.router)
api_router.include_router(media.router)
api_router.include_router(segments.router)
api_router.include_router(annotations.router)
api_router.include_router(submissions.router)
api_router.include_router(search.router)
api_router.include_router(exports.router)
api_router.include_router(takedowns.router)
api_router.include_router(text_records.router)
api_router.include_router(orthography.router)\napi_router.include_router(community.router)
