from fastapi import APIRouter, HTTPException, Query

from app.core.deps import AdminUser
from app.crawlers.scheduler import SEED_URLS, crawl_scheduler

router = APIRouter(prefix="/hunter", tags=["Gĩkũyũ corpus hunter"])


@router.get("/status")
async def hunter_status(_: AdminUser) -> dict[str, object]:
    """Return the last scheduled/manual hunter run for an administrator."""
    return {
        **crawl_scheduler.last_run,
        "scheduled": crawl_scheduler.scheduler.running,
        "seed_count": len(SEED_URLS),
        "max_pages_per_run": 1000,
    }


@router.post("/run")
async def run_hunter(
    _: AdminUser,
    max_pages: int = Query(default=250, ge=1, le=1000),
) -> dict[str, object]:
    """Run a bounded Gĩkũyũ discovery crawl immediately (admin only)."""
    if crawl_scheduler._run_lock.locked():
        raise HTTPException(status_code=409, detail="A hunter run is already in progress.")
    try:
        return await crawl_scheduler.run_web_crawl(max_pages=max_pages)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
