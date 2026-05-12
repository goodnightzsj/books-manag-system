from celery import Celery
from kombu import Queue

from app.core.config import settings


celery_app = Celery(
    "books_management_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Redis broker default visibility_timeout is 3600s: a hash of a huge file
    # running longer than that gets re-delivered to another worker and runs
    # concurrently (apply_hash_result's dedupe/merge isn't fully idempotent).
    # Bump it well above the longest expected task and give tasks a soft limit.
    broker_transport_options={"visibility_timeout": 6 * 3600},
    task_soft_time_limit=2 * 3600,
    task_time_limit=2 * 3600 + 300,
    worker_prefetch_multiplier=1,  # long jobs -> don't hoard the queue on one worker
    task_default_queue=settings.CELERY_DEFAULT_QUEUE,
    task_queues=(
        Queue(settings.BOOKS_SCAN_QUEUE),
        Queue(settings.BOOKS_ENRICH_QUEUE),
        Queue(settings.BOOKS_MAINTENANCE_QUEUE),
    ),
    imports=(
        "app.tasks.scan_tasks",
        "app.tasks.hash_tasks",
        "app.tasks.metadata_tasks",
        "app.tasks.cover_tasks",
        "app.tasks.maintenance_tasks",
    ),
    beat_schedule={
        "reconcile-stalled-jobs": {
            "task": "maintenance.reconcile_stalled_jobs",
            "schedule": settings.MAINTENANCE_RECONCILE_INTERVAL_SECONDS,
            "options": {"queue": settings.BOOKS_MAINTENANCE_QUEUE},
        }
    },
)
