"""API router for job management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas.job_schema import (
    JobStatusResponse,
    EditStructureRequest,
    EditStructureResponse,
    ConfirmGenerationResponse
)
from api.services.job_service import JobService
from api.tasks.generation_tasks import continue_generation_pipeline

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get job status and metadata.

    Args:
        job_id: Job UUID

    Returns:
        JobStatusResponse with current status and progress
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    Cancel a running job or delete completed job data.

    Args:
        job_id: Job UUID

    Returns:
        Success message
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if job can be cancelled
    if job.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="Job already completed (cannot cancel)"
        )

    # Delete job and files
    success = JobService.delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete job")

    return {"message": "Job cancelled successfully"}


@router.post("/jobs/{job_id}/edit-structure", response_model=EditStructureResponse)
async def edit_structure(
    job_id: str,
    request: EditStructureRequest,
    db: Session = Depends(get_db)
):
    """
    Submit feedback to edit presentation structure (interactive mode only).

    Args:
        job_id: Job UUID
        request: EditStructureRequest with feedback text

    Returns:
        EditStructureResponse with updated structure
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.interactive_mode:
        raise HTTPException(
            status_code=400,
            detail="Job is not in interactive mode"
        )

    if job.status != "editing":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not in editing phase (current status: {job.status})"
        )

    if not job.structure:
        raise HTTPException(
            status_code=400,
            detail="No structure available to edit"
        )

    # Import here to avoid circular dependency
    from src.voice_to_slide.structure_editor import StructureEditor
    import os

    # Edit structure using AI
    editor = StructureEditor(api_key=os.getenv("CONTENT_ANTHROPIC_API_KEY"))
    updated_structure = editor.edit_structure(
        current_structure=job.structure,
        user_feedback=request.feedback
    )

    # Save updated structure
    JobService.save_structure(db, job_id, updated_structure)

    # TODO: Track edit count for edit_number
    return EditStructureResponse(
        updated_structure=updated_structure,
        edit_number=1,
        message="Structure updated successfully"
    )


@router.post("/jobs/{job_id}/confirm-generation", response_model=ConfirmGenerationResponse)
async def confirm_generation(job_id: str, db: Session = Depends(get_db)):
    """
    Confirm structure and start PPTX generation (interactive mode only).

    Args:
        job_id: Job UUID

    Returns:
        ConfirmGenerationResponse
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "editing":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not in editing phase (current status: {job.status})"
        )

    # Update status to generating
    JobService.update_job_status(
        db=db,
        job_id=job_id,
        status="generating",
        progress_percentage=40,
        current_step="Starting PPTX generation..."
    )

    # Continue pipeline with generation
    continue_generation_pipeline(job_id=job_id)

    return ConfirmGenerationResponse(
        message="PPTX generation started",
        status="generating"
    )
