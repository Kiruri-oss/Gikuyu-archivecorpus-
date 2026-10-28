import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import api_router
from app.services.indexing import search_index
from app.crawlers.scheduler import crawl_scheduler
from app.crawlers.catalog import seed_curated_sources
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import text, select
from app.models.text_record import TextRecord
from app.services.wikimedia_import import import_random_wikipedia_pages

settings = get_settings()
configure_logging(settings.DEBUG)
logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)
_initial_import_task: asyncio.Task | None = None


async def _seed_initial_gikuyu_corpus() -> None:
    """Bootstrap an empty archive from Gĩkũyũ Wikipedia under CC BY-SA 4.0."""
    try:
        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(TextRecord.id).limit(1))
            if existing.scalar_one_or_none():
                logger.info("app.initial_corpus_seed_skipped", reason="archive already contains text")
                return
            result = await import_random_wikipedia_pages(db, "ki", 50)
            await db.commit()
            logger.info(
                "app.initial_corpus_seed_finished",
                requested=result.requested,
                imported=result.imported,
                skipped_non_gikuyu=result.skipped_non_gikuyu,
                skipped_empty=result.skipped_empty,
                skipped_duplicate_text=result.skipped_duplicate_text,
            )
    except Exception as exc:
        logger.warning("app.initial_corpus_seed_failed", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.APP_ENV)
    try:
        await search_index.ensure_indexes()
    except Exception as exc:
        logger.warning("app.search_index_init_failed", error=str(exc))
    try:
        async with AsyncSessionLocal() as db:
            added = await seed_curated_sources(db)
            await db.commit()
            logger.info("app.source_catalog_seeded", added=added)
    except Exception as exc:
        logger.warning("app.source_catalog_seed_failed", error=str(exc))
    global _initial_import_task
    if settings.APP_ENV == "production":
        # Import in the background so the API becomes available immediately.
        _initial_import_task = asyncio.create_task(_seed_initial_gikuyu_corpus())
        crawl_scheduler.start()
    yield
    if settings.APP_ENV == "production":
        crawl_scheduler.stop()
        if _initial_import_task and not _initial_import_task.done():
            _initial_import_task.cancel()
            try:
                await _initial_import_task
            except asyncio.CancelledError:
                pass
    logger.info("app.shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 🔧 FIXED: strip trailing slash + allow all headers + add PUT method
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.FRONTEND_URL).rstrip("/")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else [settings.BACKEND_URL.host],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("app.health_database_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="Persistent database is unavailable") from exc
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "persistence": "connected",
    }
