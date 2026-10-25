from contextlib import asynccontextmanager
from fastapi import FastAPI
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
from app.db.session import AsyncSessionLocal

settings = get_settings()
configure_logging(settings.DEBUG)
logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


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
    if settings.APP_ENV == "production":
        crawl_scheduler.start()
    yield
    if settings.APP_ENV == "production":
        crawl_scheduler.stop()
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
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
