from celery import Celery

from app.core.config import get_settings

settings = get_settings()

if settings.REDIS_URL is None:
    raise RuntimeError("REDIS_URL is required to start the optional Celery worker.")

celery_app = Celery(
    "gikuyu_archive",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    result_expires=86400,
)