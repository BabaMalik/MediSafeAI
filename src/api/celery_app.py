"""
Celery Application Configuration
Handles asynchronous task processing for MediSafeAI
"""

from celery import Celery
from celery.schedules import crontab
from src.config.settings import settings

# Initialize Celery app
celery_app = Celery(
    'medisafe',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'src.api.tasks',  # Import task modules
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    'monitor-privacy-budget-daily': {
        'task': 'src.api.tasks.monitor_privacy_budget',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'cleanup-old-data-weekly': {
        'task': 'src.api.tasks.cleanup_old_data',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday at 2 AM
    },
}

# Task routes (optional - for routing tasks to specific queues)
celery_app.conf.task_routes = {
    'src.api.tasks.generate_*': {'queue': 'generation'},
    'src.api.tasks.privacy_*': {'queue': 'privacy'},
    'src.api.tasks.monitor_*': {'queue': 'monitoring'},
}


if __name__ == '__main__':
    celery_app.start()
