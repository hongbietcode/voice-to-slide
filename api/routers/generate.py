"""API router for presentation generation."""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas.job_schema import JobResponse
from api.services.job_service import JobService
from api.tasks.generation_tasks import start_generation_pipeline
from api.middleware.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/v1", tags=["generation"])

# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# Allowed audio formats
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm"}


@router.post("/generate", response_model=JobResponse)
async def generate_presentation(
    request: Request,
    audio_file: UploadFile = File(...),
    theme: str = Form(default="Modern Professional"),
    include_images: bool = Form(default=True),
    interactive_mode: bool = Form(default=False),
    save_transcription: bool = Form(default=True),
    db: Session = Depends(get_db)
):
    """
    Start a new presentation generation job.

    Args:
        request: FastAPI request (for rate limiting)
        audio_file: Audio file (mp3, wav, m4a, ogg, webm)
        theme: Presentation theme (default: "Modern Professional")
        include_images: Include images from Unsplash (default: True)
        interactive_mode: Enable interactive editing (default: False)
        save_transcription: Save transcription JSON (default: True)

    Returns:
        JobResponse with job_id and status

    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 400: Invalid file format
        HTTPException 413: File too large
    """
    # Check rate limit
    await rate_limiter(request, db)
    # Validate file extension
    file_ext = Path(audio_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size (read first chunk to check)
    content = await audio_file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )

    # Save uploaded file
    storage_dir = Path(os.getenv("STORAGE_DIR", "./storage"))
    uploads_dir = storage_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())
    audio_filename = audio_file.filename
    audio_file_path = uploads_dir / job_id / audio_filename

    audio_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audio_file_path, "wb") as f:
        f.write(content)

    # Create job in database
    job = JobService.create_job(
        db=db,
        audio_filename=audio_filename,
        audio_file_path=str(audio_file_path),
        theme=theme,
        include_images=include_images,
        interactive_mode=interactive_mode,
        save_transcription=save_transcription
    )

    # Start background task
    start_generation_pipeline(
        job_id=str(job.id),
        audio_path=str(audio_file_path),
        use_images=include_images,
        interactive_mode=interactive_mode
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        message="Job created successfully",
        estimated_time_seconds=300 if not interactive_mode else 600
    )
