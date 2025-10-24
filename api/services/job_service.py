"""Service layer for job operations."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from api.models.job import Job


class JobService:
    """Service class for job operations."""

    @staticmethod
    def create_job(
        db: Session,
        audio_filename: str,
        audio_file_path: str,
        theme: str,
        include_images: bool,
        interactive_mode: bool,
        save_transcription: bool
    ) -> Job:
        """Create a new job in database."""
        job = Job(
            id=uuid.uuid4(),
            status="pending",
            audio_filename=audio_filename,
            audio_file_path=audio_file_path,
            theme=theme,
            include_images=include_images,
            interactive_mode=interactive_mode,
            save_transcription=save_transcription,
            progress_percentage=0,
            current_step="Initializing..."
        )

        # Calculate file size
        if os.path.exists(audio_file_path):
            file_size_bytes = os.path.getsize(audio_file_path)
            job.audio_file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def update_job_status(
        db: Session,
        job_id: str,
        status: str,
        progress_percentage: int,
        current_step: Optional[str] = None
    ) -> Optional[Job]:
        """Update job status and progress."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.progress_percentage = progress_percentage
            if current_step:
                job.current_step = current_step
            job.updated_at = datetime.utcnow()

            # Mark completion time
            if status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
                if job.created_at:
                    job.processing_time_seconds = int(
                        (job.completed_at - job.created_at).total_seconds()
                    )

            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def update_job_error(db: Session, job_id: str, error_message: str) -> Optional[Job]:
        """Mark job as failed with error message."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error_message
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def save_transcription(
        db: Session,
        job_id: str,
        transcription_text: str,
        transcription_json: dict
    ) -> Optional[Job]:
        """Save transcription results."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.transcription_text = transcription_text
            job.transcription_json = transcription_json
            job.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def save_structure(db: Session, job_id: str, structure: dict) -> Optional[Job]:
        """Save presentation structure."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.structure = structure
            job.total_slides = len(structure.get("slides", [])) + 1  # +1 for title slide
            job.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def save_image_data(db: Session, job_id: str, image_data: list) -> Optional[Job]:
        """Save fetched image data."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.image_data = image_data
            job.images_fetched = len([img for img in image_data if img is not None])
            job.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def save_pptx_path(
        db: Session,
        job_id: str,
        pptx_file_path: str
    ) -> Optional[Job]:
        """Save PPTX file path."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.pptx_file_path = pptx_file_path

            # Calculate file size
            if os.path.exists(pptx_file_path):
                file_size_bytes = os.path.getsize(pptx_file_path)
                job.pptx_file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

            job.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def delete_job(db: Session, job_id: str) -> bool:
        """Delete job and associated files."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            # Delete associated files
            storage_dir = os.getenv("STORAGE_DIR", "./storage")
            job_storage_path = Path(storage_dir) / "workspace" / str(job_id)

            # Delete workspace directory
            if job_storage_path.exists():
                import shutil
                shutil.rmtree(job_storage_path, ignore_errors=True)

            # Delete audio file
            if job.audio_file_path and os.path.exists(job.audio_file_path):
                os.remove(job.audio_file_path)

            # Delete PPTX file
            if job.pptx_file_path and os.path.exists(job.pptx_file_path):
                os.remove(job.pptx_file_path)

            # Delete from database
            db.delete(job)
            db.commit()
            return True
        return False
