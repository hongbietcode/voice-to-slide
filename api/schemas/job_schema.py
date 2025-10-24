"""Pydantic schemas for job API."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4


class JobCreateRequest(BaseModel):
    """Request schema for creating a new job."""
    theme: str = Field(default="Modern Professional", description="Presentation theme")
    include_images: bool = Field(default=True, description="Include images from Unsplash")
    interactive_mode: bool = Field(default=False, description="Enable interactive editing")
    save_transcription: bool = Field(default=True, description="Save transcription JSON")


class JobResponse(BaseModel):
    """Response schema for job creation."""
    job_id: str
    status: str
    message: str
    estimated_time_seconds: int = 300

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "message": "Job created successfully",
                "estimated_time_seconds": 300
            }
        }


class JobStatusResponse(BaseModel):
    """Response schema for job status."""
    job_id: str
    status: str
    progress_percentage: int
    current_step: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

    # Available after transcription
    transcription_preview: Optional[str] = None

    # Available after analysis
    structure: Optional[Dict[str, Any]] = None

    # Available after completion
    pptx_file_url: Optional[str] = None
    total_slides: Optional[int] = None
    images_fetched: Optional[int] = None
    processing_time_seconds: Optional[int] = None

    # Error details
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "analyzing",
                "progress_percentage": 30,
                "current_step": "Analyzing presentation structure",
                "created_at": "2025-10-25T12:00:00",
                "updated_at": "2025-10-25T12:02:30"
            }
        }


class EditStructureRequest(BaseModel):
    """Request schema for editing structure."""
    feedback: str = Field(..., min_length=1, description="User feedback for editing")

    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "Change slide 2 title to 'Introduction to AI' and add a bullet point about machine learning"
            }
        }


class EditStructureResponse(BaseModel):
    """Response schema for structure editing."""
    updated_structure: Dict[str, Any]
    edit_number: int
    message: str = "Structure updated successfully"

    class Config:
        json_schema_extra = {
            "example": {
                "updated_structure": {
                    "title": "AI Presentation",
                    "slides": []
                },
                "edit_number": 3,
                "message": "Structure updated successfully"
            }
        }


class ConfirmGenerationResponse(BaseModel):
    """Response schema for confirming generation."""
    message: str = "PPTX generation started"
    status: str = "generating"


class ThemeInfo(BaseModel):
    """Schema for theme information."""
    name: str
    description: str
    preview_url: str


class ThemesResponse(BaseModel):
    """Response schema for listing themes."""
    themes: List[ThemeInfo]


class ConfigCheckResponse(BaseModel):
    """Response schema for configuration check."""
    soniox_configured: bool
    anthropic_configured: bool
    unsplash_configured: bool
    playwright_installed: bool
