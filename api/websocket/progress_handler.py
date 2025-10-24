"""WebSocket progress handler for real-time updates."""

import json
import redis
from datetime import datetime
from typing import Optional, Dict, Any

# Redis client for pub/sub
redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client


def emit_progress(job_id: str, status: str, progress_percentage: int, current_step: str):
    """
    Emit progress update via Redis pub/sub.

    Args:
        job_id: Job UUID
        status: Current status
        progress_percentage: Progress (0-100)
        current_step: Description of current step
    """
    message = {
        "type": "progress",
        "job_id": job_id,
        "status": status,
        "progress_percentage": progress_percentage,
        "current_step": current_step,
        "timestamp": datetime.utcnow().isoformat()
    }

    client = get_redis_client()
    channel = f"job:{job_id}"
    client.publish(channel, json.dumps(message))


def emit_structure_ready(job_id: str, structure: Dict[str, Any]):
    """
    Emit structure ready event (interactive mode).

    Args:
        job_id: Job UUID
        structure: Presentation structure
    """
    message = {
        "type": "structure_ready",
        "job_id": job_id,
        "structure": structure,
        "message": "Structure analysis complete. You can now provide feedback or confirm to generate.",
        "timestamp": datetime.utcnow().isoformat()
    }

    client = get_redis_client()
    channel = f"job:{job_id}"
    client.publish(channel, json.dumps(message))


def emit_completed(job_id: str, pptx_file_url: str):
    """
    Emit completion event.

    Args:
        job_id: Job UUID
        pptx_file_url: URL to download PPTX
    """
    message = {
        "type": "completed",
        "job_id": job_id,
        "pptx_file_url": pptx_file_url,
        "timestamp": datetime.utcnow().isoformat()
    }

    client = get_redis_client()
    channel = f"job:{job_id}"
    client.publish(channel, json.dumps(message))


def emit_error(job_id: str, error_message: str, error_code: str):
    """
    Emit error event.

    Args:
        job_id: Job UUID
        error_message: Error description
        error_code: Error code
    """
    message = {
        "type": "error",
        "job_id": job_id,
        "error_message": error_message,
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat()
    }

    client = get_redis_client()
    channel = f"job:{job_id}"
    client.publish(channel, json.dumps(message))
