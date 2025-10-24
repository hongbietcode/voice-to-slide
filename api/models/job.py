"""Job model for database."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DECIMAL, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
from api.database import Base


class Job(Base):
    """
    Job model representing a presentation generation job.

    Status flow:
    pending → transcribing → analyzing → [editing] → generating → completed/failed
    """
    __tablename__ = "jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job metadata
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True
    )  # pending, transcribing, analyzing, editing, generating, completed, failed
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Input data
    audio_filename = Column(String(255), nullable=False)
    audio_file_path = Column(String(500), nullable=False)
    audio_file_size_mb = Column(DECIMAL(10, 2), nullable=True)
    audio_duration_seconds = Column(Integer, nullable=True)

    # Configuration
    theme = Column(String(100), default="Modern Professional")
    include_images = Column(Boolean, default=True)
    interactive_mode = Column(Boolean, default=False)
    save_transcription = Column(Boolean, default=True)

    # Processing results
    transcription_text = Column(Text, nullable=True)
    transcription_json = Column(JSON, nullable=True)  # Full transcription with timestamps
    structure = Column(JSON, nullable=True)  # Presentation structure
    image_data = Column(JSON, nullable=True)  # Array of image metadata

    # Output files
    html_files = Column(JSON, nullable=True)  # Array of HTML file paths
    image_files = Column(JSON, nullable=True)  # Array of PNG file paths
    pptx_file_path = Column(String(500), nullable=True)
    pptx_file_size_mb = Column(DECIMAL(10, 2), nullable=True)

    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    # Statistics
    total_slides = Column(Integer, nullable=True)
    images_fetched = Column(Integer, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)

    def to_dict(self):
        """Convert job to dictionary for API responses."""
        return {
            "job_id": str(self.id),
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "audio_filename": self.audio_filename,
            "theme": self.theme,
            "include_images": self.include_images,
            "interactive_mode": self.interactive_mode,
            "transcription_preview": (
                self.transcription_text[:500] + "..."
                if self.transcription_text and len(self.transcription_text) > 500
                else self.transcription_text
            ) if self.transcription_text else None,
            "structure": self.structure,
            "pptx_file_url": f"/api/v1/download/{self.id}" if self.pptx_file_path else None,
            "total_slides": self.total_slides,
            "images_fetched": self.images_fetched,
            "processing_time_seconds": self.processing_time_seconds,
            "error_message": self.error_message
        }

    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, progress={self.progress_percentage}%)>"
