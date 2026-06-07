from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "voice_generation",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.generation"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=60 * 60 * 24,
    task_always_eager=settings.celery_task_always_eager,
    task_store_eager_result=True,
)
