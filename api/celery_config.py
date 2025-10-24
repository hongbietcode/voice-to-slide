"""Celery configuration and setup."""

import os
from celery import Celery
from kombu import Exchange, Queue

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery("voice_to_slide")

# Configure Celery
celery_app.config_from_object({
    # Broker (Redis)
    "broker_url": REDIS_URL,
    "result_backend": REDIS_URL,

    # Task settings
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "enable_utc": True,

    # Retry settings
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "task_time_limit": 3600,  # 1 hour max per task
    "task_soft_time_limit": 3300,  # 55 minutes soft limit

    # Queue settings
    "task_routes": {
        "api.tasks.generation_tasks.transcribe_audio_task": {"queue": "transcription"},
        "api.tasks.generation_tasks.analyze_structure_task": {"queue": "analysis"},
        "api.tasks.generation_tasks.generate_presentation_task": {"queue": "generation"},
    },

    # Concurrency
    "worker_prefetch_multiplier": 1,  # One task at a time per worker
    "worker_max_tasks_per_child": 10,  # Restart worker after 10 tasks (prevent memory leaks)

    # Result expiration
    "result_expires": 3600,  # Results expire after 1 hour
})

# Auto-discover tasks
celery_app.autodiscover_tasks(["api.tasks"])
