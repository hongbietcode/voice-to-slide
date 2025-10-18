"""Audio transcription module using Soniox API."""

import os
import time
from pathlib import Path
from typing import Dict, Any
from soniox.speech_service import SpeechClient
from soniox.transcribe_file import transcribe_file_short, transcribe_file_async
from .utils import get_logger, save_json

logger = get_logger(__name__)

class AudioTranscriber:
    """Handles audio transcription using Soniox API."""

    def __init__(self, api_key: str | None = None):
        """Initialize the transcriber with Soniox API key.

        Args:
            api_key: Soniox API key. If None, reads from SONIOX_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("SONIOX_API_KEY")
        if not self.api_key:
            raise ValueError("Soniox API key is required. Set SONIOX_API_KEY environment variable.")

        self.client = SpeechClient(api_key=self.api_key)
        logger.info("AudioTranscriber initialized successfully")

    def transcribe(
        self,
        audio_path: Path | str,
        model: str = "en_v2",
        enable_global_speaker_diarization: bool = False
    ) -> Dict[str, Any]:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file (MP3, WAV, M4A, etc.)
            model: Soniox model to use (default: en_v2 for English)
            enable_global_speaker_diarization: Enable speaker identification

        Returns:
            Dictionary containing transcription results with keys:
                - text: Full transcription text
                - words: List of word-level timestamps (if available)
                - speakers: Speaker information (if diarization enabled)
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription of {audio_path.name}")
        logger.info(f"File size: {audio_path.stat().st_size / 1024 / 1024:.2f} MB")

        # Determine file size to choose appropriate transcription method
        file_size_mb = audio_path.stat().st_size / 1024 / 1024

        try:
            if file_size_mb < 10:  # Try synchronous for small files first
                logger.info("Using synchronous transcription (file < 10MB)")
                try:
                    result = transcribe_file_short(
                        str(audio_path),
                        self.client,
                        model=model,
                        enable_global_speaker_diarization=enable_global_speaker_diarization,
                    )
                except Exception as e:
                    # If audio duration exceeds limit for sync, fall back to async
                    if "max_audio_duration_exceeded" in str(e):
                        logger.info("Audio duration exceeds sync limit, switching to async transcription")
                        file_id = transcribe_file_async(
                            str(audio_path),
                            self.client,
                            model=model,
                            enable_global_speaker_diarization=enable_global_speaker_diarization,
                        )
                        result = self._wait_for_async_result(file_id)
                    else:
                        raise
            else:  # Use async for larger files
                logger.info("Using async transcription (file >= 10MB)")
                file_id = transcribe_file_async(
                    str(audio_path),
                    self.client,
                    model=model,
                    enable_global_speaker_diarization=enable_global_speaker_diarization,
                )
                result = self._wait_for_async_result(file_id)

            # Extract the full text from result
            if hasattr(result, 'words'):
                text = ' '.join([word.text for word in result.words])
            else:
                text = str(result)

            logger.info(f"Transcription completed. Length: {len(text)} characters")

            transcription_data = {
                "audio_file": str(audio_path),
                "text": text,
                "model": model,
                "file_size_mb": file_size_mb,
            }

            # Add word-level data if available
            if hasattr(result, 'words'):
                transcription_data["words"] = [
                    {
                        "text": word.text,
                        "start_ms": word.start_ms if hasattr(word, 'start_ms') else None,
                        "duration_ms": word.duration_ms if hasattr(word, 'duration_ms') else None,
                    }
                    for word in result.words
                ]

            # Add speaker information if available
            if enable_global_speaker_diarization and hasattr(result, 'speakers'):
                transcription_data["speakers"] = result.speakers

            return transcription_data

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    def _wait_for_async_result(self, file_id: str, max_wait_seconds: int = 300, poll_interval: int = 2):
        """Wait for async transcription to complete and return the result.

        Args:
            file_id: File ID returned from transcribe_file_async
            max_wait_seconds: Maximum time to wait for completion (default: 5 minutes)
            poll_interval: Time between status checks in seconds (default: 2 seconds)

        Returns:
            Transcription result object

        Raises:
            TimeoutError: If transcription doesn't complete within max_wait_seconds
        """
        logger.info(f"Waiting for async transcription to complete (file_id: {file_id})")
        start_time = time.time()
        
        while True:
            # Check if we've exceeded the max wait time
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                raise TimeoutError(f"Async transcription timed out after {max_wait_seconds} seconds")
            
            # Get the status
            status = self.client.GetTranscribeAsyncStatus(file_id)
            
            if status.status == "COMPLETED":
                logger.info(f"Transcription completed after {elapsed:.1f} seconds")
                result = self.client.GetTranscribeAsyncResult(file_id)
                return result
            elif status.status == "FAILED":
                error_msg = getattr(status, 'error_message', 'Unknown error')
                raise RuntimeError(f"Async transcription failed: {error_msg}")
            
            # Still processing, wait and try again
            logger.debug(f"Transcription in progress... (status: {status.status}, elapsed: {elapsed:.1f}s)")
            time.sleep(poll_interval)

    def transcribe_and_save(
        self,
        audio_path: Path | str,
        output_path: Path | str | None = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Transcribe audio and save results to JSON file.

        Args:
            audio_path: Path to the audio file
            output_path: Path to save JSON output. If None, saves next to audio file.
            **kwargs: Additional arguments passed to transcribe()

        Returns:
            Transcription data dictionary
        """
        result = self.transcribe(audio_path, **kwargs)

        if output_path is None:
            audio_path = Path(audio_path)
            output_path = audio_path.with_suffix('.transcription.json')

        save_json(result, output_path)
        logger.info(f"Transcription saved to {output_path}")

        return result
