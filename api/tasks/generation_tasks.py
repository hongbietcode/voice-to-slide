"""Celery tasks for presentation generation."""

import os
import sys
from pathlib import Path
from celery import chain

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.celery_config import celery_app
from api.database import get_db_context
from api.services.job_service import JobService
from api.websocket.progress_handler import emit_progress, emit_structure_ready, emit_completed, emit_error

from src.voice_to_slide.transcriber import AudioTranscriber
from src.voice_to_slide.presentation_orchestrator import PresentationOrchestrator
from src.voice_to_slide.image_fetcher import ImageFetcher
from src.voice_to_slide.html_generator import HTMLSlideGenerator
from src.voice_to_slide.html_to_pptx import HTMLToPPTXConverter


@celery_app.task(bind=True, max_retries=3)
def transcribe_audio_task(self, job_id: str, audio_path: str):
    """
    Step 1: Transcribe audio using Soniox API.

    Args:
        job_id: Job UUID
        audio_path: Path to audio file

    Returns:
        dict with job_id and transcription result
    """
    try:
        # Update job status
        with get_db_context() as db:
            JobService.update_job_status(
                db, job_id, "transcribing", 10, "Transcribing audio..."
            )
        emit_progress(job_id, "transcribing", 10, "Transcribing audio...")

        # Call existing module
        transcriber = AudioTranscriber(api_key=os.getenv("SONIOX_API_KEY"))
        result = transcriber.transcribe(audio_path)

        # Save to database
        with get_db_context() as db:
            JobService.save_transcription(
                db,
                job_id,
                result["text"],
                result
            )

        # Update progress
        with get_db_context() as db:
            JobService.update_job_status(
                db, job_id, "analyzing", 25, "Transcription complete"
            )
        emit_progress(job_id, "analyzing", 25, "Transcription complete")

        return {"job_id": job_id, "transcription_text": result["text"]}

    except Exception as e:
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        else:
            # Mark as failed
            with get_db_context() as db:
                JobService.update_job_error(db, job_id, str(e))
            emit_error(job_id, str(e), "TRANSCRIPTION_FAILED")
            raise


@celery_app.task(bind=True)
def analyze_structure_task(self, prev_result: dict, use_images: bool, interactive_mode: bool):
    """
    Step 2: Analyze structure using Claude Tool Use.

    Args:
        prev_result: Result from transcribe_audio_task containing job_id and transcription_text
        use_images: Whether to include images
        interactive_mode: Whether to wait for user confirmation

    Returns:
        dict with job_id and structure
    """
    # Unpack result from previous task
    job_id = prev_result["job_id"]
    transcription_text = prev_result["transcription_text"]

    try:
        with get_db_context() as db:
            JobService.update_job_status(
                db, job_id, "analyzing", 30, "Analyzing content structure..."
            )
        emit_progress(job_id, "analyzing", 30, "Analyzing content structure...")

        # Call existing module
        orchestrator = PresentationOrchestrator(
            api_key=os.getenv("CONTENT_ANTHROPIC_API_KEY")
        )
        result = orchestrator.analyze_and_structure(transcription_text, use_images)

        # Save structure to database
        with get_db_context() as db:
            JobService.save_structure(db, job_id, result["structure"])

        # Check if interactive mode
        if interactive_mode:
            # Emit structure_ready event and wait
            with get_db_context() as db:
                JobService.update_job_status(
                    db, job_id, "editing", 35, "Waiting for user confirmation..."
                )
            emit_structure_ready(job_id, result["structure"])
            # Task ends here - user must call confirm_generation endpoint
            return {"job_id": job_id, "awaiting_confirmation": True}
        else:
            # Auto-confirm, proceed to generation
            with get_db_context() as db:
                JobService.update_job_status(
                    db, job_id, "generating", 40, "Starting generation..."
                )
            return {"job_id": job_id, "structure": result["structure"]}

    except Exception as e:
        with get_db_context() as db:
            JobService.update_job_error(db, job_id, str(e))
        emit_error(job_id, str(e), "ANALYSIS_FAILED")
        raise


@celery_app.task(bind=True)
def generate_presentation_task(self, prev_result):
    """
    Step 3: Generate PPTX (after confirmation).

    Args:
        prev_result: Either dict from analyze_structure_task or string job_id

    Returns:
        dict with job_id and pptx_path
    """
    # Handle both dict and string inputs for flexibility
    if isinstance(prev_result, dict):
        job_id = prev_result["job_id"]
    else:
        job_id = prev_result

    try:
        # Get job details
        with get_db_context() as db:
            job = JobService.get_job(db, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            structure = job.structure
            theme = job.theme
            include_images = job.include_images

        storage_dir = Path(os.getenv("STORAGE_DIR", "./storage"))
        workspace_dir = storage_dir / "workspace" / job_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # Sub-step 1: Fetch images
        with get_db_context() as db:
            JobService.update_job_status(
                db, job_id, "generating", 45, "Fetching images..."
            )
        emit_progress(job_id, "generating", 45, "Fetching images...")

        if include_images:
            fetcher = ImageFetcher(api_key=os.getenv("UNSPLASH_ACCESS_KEY"))
            image_queries = [slide.get("image_theme") for slide in structure["slides"]]
            image_data = fetcher.get_image_urls_for_presentation(image_queries)
            with get_db_context() as db:
                JobService.save_image_data(db, job_id, image_data)
        else:
            image_data = []

        # Sub-step 2: Generate HTML
        with get_db_context() as db:
            JobService.update_job_status(
                db, job_id, "generating", 60, "Generating HTML slides..."
            )
        emit_progress(job_id, "generating", 60, "Generating HTML slides...")

        generator = HTMLSlideGenerator(
            api_key=os.getenv("CONTENT_ANTHROPIC_API_KEY"),
            workspace_dir=str(workspace_dir)
        )
        html_files = generator.generate_slides_html(
            structure=structure,
            image_data=image_data,
            theme=theme,
            output_dir=workspace_dir / "slides"
        )

        # Sub-step 3: Render to PNG and assemble PPTX
        with get_db_context() as db:
            JobService.update_job_status(
                db, job_id, "generating", 80, "Rendering slides to images..."
            )
        emit_progress(job_id, "generating", 80, "Rendering slides to images...")

        outputs_dir = storage_dir / "outputs" / job_id
        outputs_dir.mkdir(parents=True, exist_ok=True)
        output_path = outputs_dir / "presentation.pptx"

        converter = HTMLToPPTXConverter()
        converter.convert_html_files_to_pptx(
            html_files=html_files,
            output_path=output_path,
            image_dir=workspace_dir / "slide_images"
        )

        # Update job as completed
        with get_db_context() as db:
            JobService.save_pptx_path(db, job_id, str(output_path))
            JobService.update_job_status(
                db, job_id, "completed", 100, "Presentation generated successfully"
            )
        emit_completed(job_id, f"/api/v1/download/{job_id}")

        return {"job_id": job_id, "pptx_path": str(output_path)}

    except Exception as e:
        with get_db_context() as db:
            JobService.update_job_error(db, job_id, str(e))
        emit_error(job_id, str(e), "GENERATION_FAILED")
        raise


def start_generation_pipeline(job_id: str, audio_path: str, use_images: bool, interactive_mode: bool):
    """
    Start the generation pipeline (chain tasks together).

    For non-interactive mode, all tasks run in sequence.
    For interactive mode, pipeline pauses at analyze_structure_task.
    """
    if interactive_mode:
        # Only run transcription and analysis
        chain(
            transcribe_audio_task.s(job_id, audio_path),
            analyze_structure_task.s(use_images, interactive_mode)
        ).apply_async()
    else:
        # Run full pipeline
        chain(
            transcribe_audio_task.s(job_id, audio_path),
            analyze_structure_task.s(use_images, interactive_mode),
            generate_presentation_task.s()
        ).apply_async()


def continue_generation_pipeline(job_id: str):
    """
    Continue pipeline after user confirmation (interactive mode).
    """
    generate_presentation_task.apply_async(args=[job_id])
