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
    '--theme', '-t',
    type=click.Choice([
        'Modern Professional',
        'Dark Mode',
        'Vibrant Creative',
        'Minimal Clean',
        'Corporate Blue'
    ], case_sensitive=False),
    default='Modern Professional',
    help='Presentation theme (default: Modern Professional)'
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
@click.option(
    '--interactive/--no-interactive',
    default=False,
    help='Enable interactive editing of structure before generation (default: disabled)'
)
def generate(audio_file, output, theme, images, save_transcription, interactive):
    """Generate a presentation from an audio file.

    AUDIO_FILE: Path to the audio file (MP3, WAV, M4A, etc.)

    Example:
        voice-to-slide generate meeting.mp3
        voice-to-slide generate presentation.wav --output slides.pptx
        voice-to-slide generate recording.mp3 --theme "Dark Mode"
        voice-to-slide generate recording.mp3 --theme "Vibrant Creative" --no-images
        voice-to-slide generate recording.mp3 --interactive
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

        # Get structure
        result = orchestrator.analyze_and_structure(transcription_text, use_images=images)
        structure = result["structure"]

        # Show initial preview
        preview = orchestrator.format_structure_preview(structure)
        click.echo(preview)
        click.echo()

        # Step 3: Interactive feedback loop (if enabled)
        if interactive:
            click.echo("💬 FEEDBACK MODE")
            click.echo("=" * 50)
            click.echo("You can now provide feedback to edit the structure.")
            click.echo("Type your feedback and press Enter.")
            click.echo("Type '/start' when ready to generate slides.")
            click.echo("=" * 50)
            click.echo()

            # Callback to get feedback from user
            def get_feedback():
                return input("\n📝 Feedback (or /start to begin): ").strip()

            # Callback to show updated structure
            def show_structure(updated_structure):
                click.echo("\n✨ Structure updated!")
                click.echo("=" * 70)
                preview = orchestrator.format_structure_preview(updated_structure)
                click.echo(preview)

            # Run feedback loop
            structure = orchestrator.allow_feedback_loop(
                structure,
                get_feedback,
                show_structure
            )

            # Show final structure after edits
            click.echo("\n" + "=" * 70)
            click.echo("✅ FINAL STRUCTURE - Ready to generate slides!")
            click.echo("=" * 70)
            click.echo()
        else:
            # Step 3 (non-interactive): Confirm generation
            if not click.confirm('\n⚠️  Proceed with presentation generation?', default=True):
                click.echo("\n❌ Generation cancelled by user.")
                sys.exit(0)

            click.echo()

        # Step 4: Generate presentation locally (Strategy B with HTML)
        click.echo("🎨 Step 4: Generating presentation (Strategy B: HTML → Images → PPTX)...")
        click.echo(f"   • Theme: {theme}")
        if interactive:
            click.echo(f"   • Using edited structure from feedback loop")
        click.echo(f"   • Generating HTML slides with Claude Messages API")
        click.echo(f"   • Rendering HTML to high-quality images (Playwright)")
        click.echo(f"   • Fetching images from Unsplash")
        click.echo(f"   • Creating PPTX with rendered slides")
        click.echo()

        # Generate with structure (either original or edited)
        result = orchestrator.generate_presentation(
            output_path=output,
            use_images=images,
            theme=theme,
            use_html_generation=True,
            structure=structure  # Pass the structure (edited or original)
        )

        if result['status'] == 'success':
            click.echo()
            click.echo(f"✅ Success! Presentation generated:")
            click.echo(f"   📄 File: {result['output_path']}")
            click.echo(f"   🎨 Theme: {result.get('theme', 'N/A')}")
            click.echo(f"   📊 Total slides: {result['total_slides']}")
            click.echo(f"   🖼️  Images: {result['images_fetched']}/{len(result['structure'].get('slides', []))}")
            if 'html_files' in result:
                click.echo(f"   📝 HTML files: {len(result['html_files'])} generated")
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
