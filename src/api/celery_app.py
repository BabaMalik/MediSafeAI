"""
Celery Application
Handles asynchronous tasks for MediSafeAI
"""

import os
from celery import Celery
from src.config.settings import settings

# Create Celery instance
celery_app = Celery(
    'medisafe',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
)

# Autodiscover tasks
celery_app.autodiscover_tasks(['src.api.tasks'])
