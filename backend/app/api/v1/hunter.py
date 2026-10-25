from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.core.deps import AdminUser
from app.crawlers.scheduler import SEED_URLS, crawl_scheduler
from app.crawlers.web import MAX_DISCOVERY_HOSTS, MAX_PAGES_PER_HOST

router = APIRouter(prefix="/hunter", tags=["Gĩkũyũ corpus hunter"])


@router.get("/status")
async def hunter_status(_: AdminUser) -> dict[str, object]:
    """Return the latest automatic or manually triggered hunter run."""
    return {
        **crawl_scheduler.last_run,
        "scheduled": crawl_scheduler.scheduler.running,
        "seed_count": len(SEED_URLS),
        "default_page_budget": 500,
        "max_pages_per_run": 1000,
        "max_discovery_hosts": MAX_DISCOVERY_HOSTS,
        "max_pages_per_host": MAX_PAGES_PER_HOST,
    }


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_hunter(
    background_tasks: BackgroundTasks,
    _: AdminUser,
    max_pages: int = Query(default=500, ge=1, le=1000),
) -> dict[str, object]:
    """Queue a bounded Gĩkũyũ crawl without holding the admin HTTP request open."""
    previous_status = crawl_scheduler.last_run.get("status")
    if crawl_scheduler._run_lock.locked() or previous_status in {"queued", "running"}:
        raise HTTPException(status_code=409, detail="A hunter run is already in progress.")
    crawl_scheduler.last_run = {
        "status": "queued",
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "page_budget": max_pages,
    }
    background_tasks.add_task(crawl_scheduler.run_web_crawl, max_pages=max_pages)
    return {"status": "queued", "page_budget": max_pages}
