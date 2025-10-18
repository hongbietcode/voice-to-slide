"""Main CLI interface for voice-to-slide application."""

import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv

from .transcriber import AudioTranscriber
from .presentation_generator import PresentationGenerator
from .image_fetcher import ImageFetcher
from .content_summarizer import ContentSummarizer
from .utils import get_logger, sanitize_filename, ensure_directory

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Voice-to-Slide: Convert voice recordings into professional presentations.

    This tool transcribes audio files and automatically generates PowerPoint
    presentations using Claude AI with the PPTX skill.
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
    '--enhance/--no-enhance',
    default=True,
    help='Enhance slide content quality (default: enabled)'
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
def generate(audio_file, output, enhance, images, save_transcription):
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

        # Step 1.5: Breakdown and Summarize
        click.echo("📊 Step 1.5: Breaking down and summarizing content...")
        try:
            summarizer = ContentSummarizer()
            breakdown = summarizer.breakdown_and_summarize(transcription_text)
            
            click.echo(f"\n   ✅ Executive Summary:")
            click.echo(f"      {breakdown.get('executive_summary', 'N/A')}")
            
            click.echo(f"\n   📌 Key Points ({len(breakdown.get('key_points', []))}):")
            for i, point in enumerate(breakdown.get('key_points', [])[:5], 1):
                click.echo(f"      {i}. {point}")
            
            click.echo(f"\n   🏷️  Main Topics: {', '.join(breakdown.get('main_topics', []))}")
            
            structure = breakdown.get('recommended_structure', {})
            click.echo(f"\n   📋 Recommended Structure: {structure.get('total_slides', 8)} slides")
            click.echo(f"      - Intro: {structure.get('intro_slides', 1)} | Content: {structure.get('content_slides', 6)} | Conclusion: {structure.get('conclusion_slides', 1)}")
            
            # Save breakdown to file
            breakdown_path = output.with_suffix('.breakdown.json')
            from .utils import save_json
            save_json(breakdown, breakdown_path)
            click.echo(f"\n   💾 Saved breakdown to: {breakdown_path}")
            
            click.echo()
        except Exception as e:
            click.echo(f"   ⚠️  Failed to breakdown content: {e}")
            click.echo(f"   Continuing with basic analysis...")
            breakdown = None
        
        # Step 2: Analyze content
        click.echo("🧠 Step 2: Analyzing content for presentation structure...")
        generator = PresentationGenerator()
        analysis = generator.analyze_transcription(transcription_text)

        click.echo(f"   Title: {analysis.get('title', 'N/A')}")
        click.echo(f"   Suggested slides: {analysis.get('num_slides', 'N/A')}")
        click.echo()

        # Step 3: Fetch images (optional)
        image_queries = None
        if images:
            click.echo("🖼️  Step 3: Fetching relevant images...")
            try:
                image_themes = analysis.get('image_themes', [])
                if image_themes:
                    fetcher = ImageFetcher()
                    image_paths = fetcher.fetch_images_for_presentation(image_themes)
                    successful = sum(1 for p in image_paths if p is not None)
                    click.echo(f"   Fetched {successful}/{len(image_themes)} images")
                    image_queries = image_themes
                else:
                    click.echo("   No image themes suggested, skipping...")
            except ValueError as e:
                click.echo(f"   ⚠️  Skipping images: {e}")
                images = False
            click.echo()

        # Step 3.5: Show preview and confirm
        click.echo("📋 Step 3.5: Preview & Confirmation")
        click.echo("=" * 70)
        
        # Show breakdown if available
        if breakdown:
            click.echo(f"\n📝 CONTENT BREAKDOWN:")
            click.echo(f"   Summary: {breakdown.get('executive_summary', 'N/A')[:100]}...")
            click.echo(f"   Audience: {breakdown.get('audience', 'N/A')}")
            click.echo(f"   Tone: {breakdown.get('tone', 'N/A')}")
            
            # Show detailed sections from breakdown
            sections_detail = breakdown.get('sections', [])
            if sections_detail:
                click.echo(f"\n📑 CONTENT SECTIONS ({len(sections_detail)} sections):")
                for i, section in enumerate(sections_detail[:3], 1):  # Show first 3
                    click.echo(f"   {i}. {section.get('title', 'Section')}")
                    click.echo(f"      → {section.get('key_info', '')[:80]}...")
                if len(sections_detail) > 3:
                    click.echo(f"   ... and {len(sections_detail) - 3} more sections")
        
        click.echo(f"\n📊 PRESENTATION PLAN:")
        click.echo(f"   • Title: {analysis.get('title', 'N/A')}")
        click.echo(f"   • Number of slides: {analysis.get('num_slides', 'N/A')}")
        click.echo(f"   • Enhancement mode: {'enabled' if enhance else 'disabled'}")
        
        sections = analysis.get('sections', [])
        if sections:
            click.echo(f"\n📑 PRESENTATION SECTIONS:")
            for i, section in enumerate(sections, 1):
                click.echo(f"   {i}. {section}")
        
        key_messages = analysis.get('key_messages', [])
        if key_messages:
            click.echo(f"\n💡 KEY MESSAGES:")
            for i, msg in enumerate(key_messages, 1):
                click.echo(f"   {i}. {msg}")
        
        if image_queries:
            click.echo(f"\n🖼️  IMAGE THEMES:")
            for i, theme in enumerate(image_queries, 1):
                click.echo(f"   {i}. {theme}")
        
        # Show the actual prompt that will be sent
        click.echo(f"\n📝 PROMPT TO BE SENT TO CLAUDE:")
        click.echo("-" * 70)
        
        # Use enhanced prompt if breakdown available
        if breakdown:
            try:
                preview_prompt = ContentSummarizer().create_enhanced_prompt(
                    transcription_text,
                    breakdown
                )
                click.echo("   (Using enhanced prompt with breakdown)")
            except Exception:
                preview_prompt = generator.preview_prompt(
                    transcription_text,
                    image_queries=image_queries if images else None,
                    enhance=enhance
                )
        else:
            preview_prompt = generator.preview_prompt(
                transcription_text,
                image_queries=image_queries if images else None,
                enhance=enhance
            )
        
        # Show first 500 chars of prompt for preview
        prompt_preview = preview_prompt[:500] + "..." if len(preview_prompt) > 500 else preview_prompt
        click.echo(prompt_preview)
        click.echo("-" * 70)
        click.echo(f"   (Total prompt length: {len(preview_prompt)} characters)")
        
        click.echo("\n" + "=" * 70)
        
        # Ask for confirmation
        if not click.confirm('\n⚠️  Proceed with presentation generation?', default=True):
            click.echo("\n❌ Generation cancelled by user.")
            sys.exit(0)
        
        click.echo()

        # Step 4: Generate presentation
        click.echo("🎨 Step 4: Generating presentation...")
        click.echo(f"   Using Claude with PPTX skill...")
        click.echo(f"   Enhancement: {'enabled' if enhance else 'disabled'}")
        
        # Use enhanced prompt if breakdown is available
        if breakdown:
            click.echo(f"   Using enhanced prompt with content breakdown")
            try:
                enhanced_prompt = ContentSummarizer().create_enhanced_prompt(
                    transcription_text,
                    breakdown
                )
                # We'll pass the enhanced context through image_queries metadata
                # (This is a workaround - ideally we'd add a breakdown parameter)
                result = generator.generate_presentation(
                    enhanced_prompt,  # Use enhanced prompt instead of raw transcription
                    image_queries=image_queries if images else None,
                    output_path=output,
                    enhance=enhance
                )
            except Exception as e:
                click.echo(f"   ⚠️  Enhanced prompt failed, using standard generation: {e}")
                result = generator.generate_presentation(
                    transcription_text,
                    image_queries=image_queries if images else None,
                    output_path=output,
                    enhance=enhance
                )
        else:
            result = generator.generate_presentation(
                transcription_text,
                image_queries=image_queries if images else None,
                output_path=output,
                enhance=enhance
            )

        if result['status'] == 'success':
            click.echo()
            click.echo(f"✅ Success! Presentation saved to: {output}")
            if result.get('file_id'):
                click.echo(f"   File ID: {result['file_id']}")
        else:
            click.echo()
            click.echo(f"⚠️  Presentation generated with warnings")
            click.echo(f"   Check the output file: {output}")

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
        "Anthropic Claude API": "CONTENT_ANTHROPIC_API_KEY",
        "Presentation Anthropic API": "PRESENTATION_ANTHROPIC_API_KEY",
        "Unsplash API": "UNSPLASH_ACCESS_KEY"
    }

    all_configured = True

    for name, env_var in keys.items():
        value = os.getenv(env_var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            click.echo(f"✅ {name:20} {masked}")
        else:
            click.echo(f"❌ {name:20} Not configured")
            all_configured = False

    click.echo()
    if all_configured:
        click.echo("✅ All API keys are configured!")
    else:
        click.echo("⚠️  Some API keys are missing. Check .env file.")
        click.echo("   Copy .env.example to .env and add your API keys.")
        sys.exit(1)


if __name__ == "__main__":
    cli()
