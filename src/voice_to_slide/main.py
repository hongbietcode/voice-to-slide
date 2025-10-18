"""Main CLI interface for voice-to-slide application."""

import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv

from .transcriber import AudioTranscriber
from .presentation_orchestrator import PresentationOrchestrator
from .utils import get_logger, sanitize_filename, ensure_directory

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Voice-to-Slide: Convert voice recordings into professional presentations.

    This tool transcribes audio files and automatically generates PowerPoint
    presentations using Claude AI Tool Use and local python-pptx generation.
    """
    pass


@cli.command()
@click.argument('audio_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output PPTX file path (default: ./output/<audio_name>.pptx)'
)
@click.option(
    '--images/--no-images',
    default=True,
    help='Include relevant images from Unsplash (default: enabled)'
)
@click.option(
    '--save-transcription/--no-save-transcription',
    default=True,
    help='Save transcription to JSON file (default: enabled)'
)
def generate(audio_file, output, images, save_transcription):
    """Generate a presentation from an audio file.

    AUDIO_FILE: Path to the audio file (MP3, WAV, M4A, etc.)

    Example:
        voice-to-slide generate meeting.mp3
        voice-to-slide generate presentation.wav --output slides.pptx
    """
    try:
        click.echo(f"🎙️  Voice-to-Slide Generator")
        click.echo(f"{'=' * 50}")
        click.echo(f"Audio file: {audio_file}")
        click.echo()

        # Determine output path
        if output is None:
            output_dir = Path("output")
            ensure_directory(output_dir)
            filename = sanitize_filename(audio_file.stem) + ".pptx"
            output = output_dir / filename

        # Step 1: Transcribe audio
        click.echo("📝 Step 1: Transcribing audio...")
        transcriber = AudioTranscriber()
        transcription = transcriber.transcribe(audio_file)

        if save_transcription:
            transcription_path = output.with_suffix('.transcription.json')
            from .utils import save_json
            save_json(transcription, transcription_path)
            click.echo(f"   Saved transcription to: {transcription_path}")

        transcription_text = transcription['text']
        click.echo(f"   Transcribed {len(transcription_text)} characters")
        click.echo()

        # Step 2: Analyze and preview structure using Orchestrator
        click.echo("🧠 Step 2: Analyzing content and generating structure...")
        orchestrator = PresentationOrchestrator()
        
        # Get preview
        preview = orchestrator.preview_structure(transcription_text, use_images=images)
        click.echo(preview)
        click.echo()
        
        # Step 3: Confirm generation
        if not click.confirm('\n⚠️  Proceed with presentation generation?', default=True):
            click.echo("\n❌ Generation cancelled by user.")
            sys.exit(0)
        
        click.echo()

        # Step 4: Generate presentation locally (Strategy B)
        click.echo("🎨 Step 3: Generating presentation (Strategy B: Local Generation)...")
        click.echo(f"   • Using Claude Tool Use for structure analysis")
        click.echo(f"   • Fetching images locally with network access")
        click.echo(f"   • Building PPTX locally with python-pptx")
        click.echo()
        
        result = orchestrator.generate_presentation(
            transcription_text,
            output_path=output,
            use_images=images
        )

        if result['status'] == 'success':
            click.echo()
            click.echo(f"✅ Success! Presentation generated:")
            click.echo(f"   📄 File: {result['output_path']}")
            click.echo(f"   📊 Total slides: {result['total_slides']}")
            click.echo(f"   🖼️  Images: {result['images_fetched']}/{len(result['structure'].get('slides', []))}")
        else:
            click.echo()
            click.echo(f"❌ Generation failed: {result.get('error')}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        logger.exception("Generation failed")
        sys.exit(1)


@cli.command()
@click.argument('audio_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output JSON file path'
)
def transcribe(audio_file, output):
    """Transcribe an audio file to text.

    AUDIO_FILE: Path to the audio file

    Example:
        voice-to-slide transcribe recording.mp3
        voice-to-slide transcribe audio.wav --output transcript.json
    """
    try:
        click.echo(f"📝 Transcribing: {audio_file}")

        transcriber = AudioTranscriber()
        transcription = transcriber.transcribe(audio_file)

        # Determine output path
        if output is None:
            output = audio_file.with_suffix('.transcription.json')

        from .utils import save_json
        save_json(transcription, output)

        click.echo(f"✅ Transcription saved to: {output}")
        click.echo(f"   Characters: {len(transcription['text'])}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Transcription failed")
        sys.exit(1)


@cli.command()
def check():
    """Check if all required API keys are configured."""
    click.echo("🔍 Checking configuration...")
    click.echo()

    keys = {
        "Soniox API": "SONIOX_API_KEY",
        "Claude AI": "CONTENT_ANTHROPIC_API_KEY",
        "Unsplash Images": "UNSPLASH_ACCESS_KEY"
    }

    all_configured = True

    for name, env_var in keys.items():
        value = os.getenv(env_var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            click.echo(f"✅ {name:30} {masked}")
        else:
            click.echo(f"❌ {name:30} Not configured")
            all_configured = False

    click.echo()
    if all_configured:
        click.echo("✅ All required API keys are configured!")
    else:
        click.echo("⚠️  Some required API keys are missing. Check .env file.")
        click.echo("   Copy .env.example to .env and add your API keys.")
        sys.exit(1)


if __name__ == "__main__":
    cli()
