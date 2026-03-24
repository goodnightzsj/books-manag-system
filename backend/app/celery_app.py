from celery import Celery
from kombu import Queue

from app.core.config import settings


celery_app = Celery(
    "books_management_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
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
