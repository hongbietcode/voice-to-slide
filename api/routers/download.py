"""API router for file downloads."""

import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from api.database import get_db
from api.services.job_service import JobService

router = APIRouter(prefix="/api/v1", tags=["download"])


@router.get("/download/{job_id}")
async def download_pptx(job_id: str, db: Session = Depends(get_db)):
    """
    Download the generated PPTX file.

    Args:
        job_id: Job UUID

    Returns:
        FileResponse with PPTX file
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.pptx_file_path:
        raise HTTPException(status_code=404, detail="PPTX file not ready")

    if not os.path.exists(job.pptx_file_path):
        raise HTTPException(status_code=410, detail="File expired or deleted")

    # Generate filename
    filename = f"{job.audio_filename.rsplit('.', 1)[0]}.pptx"

    return FileResponse(
        path=job.pptx_file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename
    )


@router.get("/download/{job_id}/transcription")
async def download_transcription(job_id: str, db: Session = Depends(get_db)):
    """
    Download transcription JSON.

    Args:
        job_id: Job UUID

    Returns:
        JSON with transcription data
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.transcription_json:
        raise HTTPException(status_code=404, detail="Transcription not available")

    return JSONResponse(content=job.transcription_json)


@router.get("/preview/{job_id}/slide/{slide_number}")
async def preview_slide(
    job_id: str,
    slide_number: int,
    db: Session = Depends(get_db)
):
    """
    Preview individual slide as PNG image.

    Args:
        job_id: Job UUID
        slide_number: Slide number (0-indexed)

    Returns:
        FileResponse with PNG image
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.image_files or slide_number >= len(job.image_files):
        raise HTTPException(status_code=404, detail="Slide preview not available")

    slide_image_path = job.image_files[slide_number]
    if not os.path.exists(slide_image_path):
        raise HTTPException(status_code=410, detail="Slide image expired or deleted")

    return FileResponse(
        path=slide_image_path,
        media_type="image/png",
        filename=f"slide_{slide_number:02d}.png"
    )
