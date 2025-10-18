# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice-to-Slide is a Python CLI application that converts voice recordings into professional PowerPoint presentations using AI. It orchestrates multiple AI services (Soniox for transcription, Claude for content analysis and presentation generation via PPTX skill, Unsplash for images).

**Package Manager**: This project uses [uv](https://github.com/astral-sh/uv) - an extremely fast Python package installer and resolver written in Rust.

## Development Commands

### Setup and Installation
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: pip install uv

# Install dependencies (creates .venv automatically)
uv sync

# Configure API keys
cp .env.example .env
# Edit .env to add: SONIOX_API_KEY, CONTENT_ANTHROPIC_API_KEY, PRESENTATION_ANTHROPIC_API_KEY, UNSPLASH_ACCESS_KEY

# Verify configuration
uv run voice-to-slide check
```

### Running the Application
```bash
# Generate presentation from audio
uv run voice-to-slide generate <audio-file>

# With options
uv run voice-to-slide generate audio.mp3 --output slides.pptx --no-images --no-enhance

# Transcribe only
uv run voice-to-slide transcribe audio.mp3

# Check API configuration
uv run voice-to-slide check
```

### Testing and Development
```bash
# Run the CLI directly during development
uv run python -m voice_to_slide.main generate recording.mp3

# Access individual modules (for testing)
uv run python -c "from voice_to_slide.transcriber import AudioTranscriber; print(AudioTranscriber.__doc__)"

# Install additional dev dependencies
uv add --dev pytest pytest-cov black ruff

# Run tests (if available)
uv run pytest

# Format code
uv run black src/
uv run ruff check src/
```

### Working with Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Show dependency tree
uv tree
```

## Architecture

### Pipeline Flow

The application follows a multi-stage pipeline that transforms audio into presentations:

1. **Audio Transcription** (transcriber.py)
   - Uses Soniox API for high-accuracy speech-to-text
   - Handles both sync (<10MB) and async transcription automatically
   - Outputs: transcription text + word-level timestamps

2. **Content Analysis** (content_summarizer.py, presentation_analyzer.py)
   - **ContentSummarizer**: Uses Tool Use (JSON mode) to create structured breakdown with executive summary, key points, sections, audience, tone
   - **PresentationAnalyzer**: Uses Tool Use to extract presentation structure (title, num_slides, sections, key_messages, image_themes)
   - Both use prompt caching for efficiency with large transcriptions

3. **Image Fetching** (image_fetcher.py)
   - Searches Unsplash API based on image_themes from analysis
   - Downloads, resizes (max 1920x1080), and caches images in `.cache/images/`
   - Naming convention: `slide_00_*.jpg`, `slide_01_*.jpg`, etc.

4. **Presentation Generation** (presentation_generator.py)
   - Uses Claude with PPTX skill (either Anthropic default or custom skill)
   - Constructs enhanced prompts using content breakdown
   - Leverages prompt caching for transcription content
   - Downloads generated PPTX file using Files API

### Key Architectural Patterns

**Multi-API Key Strategy**: The project uses separate API keys for different Claude operations:
- `CONTENT_ANTHROPIC_API_KEY` / `SUMMARY_ANTHROPIC_API_KEY`: For content analysis/summarization
- `PRESENTATION_ANTHROPIC_API_KEY`: For PPTX generation
This allows using different accounts/rate limits for different workloads.

**Tool Use for Structured Output**: Uses Anthropic's Tool Use feature to guarantee valid JSON responses from Claude (in content_summarizer.py and presentation_analyzer.py). This eliminates JSON parsing errors.

**Prompt Caching**: Implements prompt caching on large transcription text to reduce costs and improve performance on multi-step analysis.

**Custom Skills Support**: Supports both Anthropic's default PPTX skill and custom uploaded skills via `CUSTOM_PPTX_SKILL_ID` env var. Custom skill lives in `skills/pptx-enhanced/`.

**Image Caching Strategy**: Pre-fetches images to `.cache/images/` before presentation generation, allowing the PPTX skill to reference local cached images rather than fetching during generation.

### File Structure

```
src/voice_to_slide/
├── main.py                      # CLI interface (Click)
├── transcriber.py               # Soniox integration
├── content_summarizer.py        # Tool Use for content breakdown
├── presentation_analyzer.py     # Tool Use for structure analysis
├── presentation_generator.py    # Claude PPTX skill integration
├── image_fetcher.py            # Unsplash integration with caching
├── slide_builder.py            # (Future: manual slide building)
└── utils.py                    # Logging, file I/O helpers
```

### Critical Implementation Details

**Async Transcription Handling** (transcriber.py:128-164): The `_wait_for_async_result()` method polls Soniox for completion with timeout handling. File size threshold is 10MB between sync/async.

**File Download from Claude** (presentation_generator.py:280-304): Uses `client.beta.files.download()` with `betas=["files-api-2025-04-14"]` and extracts file_id from `bash_code_execution_tool_result` content blocks.

**Enhanced Prompt Generation** (content_summarizer.py:168-225): The `create_enhanced_prompt()` method transforms the structured breakdown into a detailed prompt that guides the PPTX skill on structure, tone, and key messages.

**Image Path Convention** (image_fetcher.py:219): Images are named `slide_{index:02d}_{photo_id}.jpg` so the PPTX skill can easily locate them by slide number.

## Environment Variables

Required:
- `SONIOX_API_KEY`: Soniox transcription API
- `CONTENT_ANTHROPIC_API_KEY` or `SUMMARY_ANTHROPIC_API_KEY`: For content analysis
- `PRESENTATION_ANTHROPIC_API_KEY`: For PPTX generation
- `UNSPLASH_ACCESS_KEY`: For image fetching (optional but recommended)

Optional:
- `CUSTOM_PPTX_SKILL_ID`: Use custom PPTX skill instead of Anthropic default
- `PRESENTATION_ANTHROPIC_BASE_URL`: Custom API endpoint/proxy
- `SUMMARY_ANTHROPIC_BASE_URL`: Custom endpoint for summarization
- `PRESENTATION_MODEL`: Override default model (default: claude-haiku-4-5-20251001)
- `SUMMARY_MODEL`: Override summarization model (default: claude-3-5-sonnet-20241022)

## Custom Skills

The project includes `.claude/skills/pptx-enhanced/` with enhanced PPTX generation capabilities:
- Support for cached Unsplash images from `.cache/images/`
- Chart generation with matplotlib
- HTML to PPTX conversion workflow
- Complete examples and helper functions
- See SKILL_SETUP.md for uploading custom skills to Anthropic

To use custom skill:
1. Upload skill using Anthropic Skills API or SDK (see SKILL_SETUP.md):
   ```bash
   uv run python upload_skill.py
   ```
2. Set `CUSTOM_PPTX_SKILL_ID=skill_01...` in .env
3. The system automatically uses custom skill if ID is present
4. If not set, defaults to Anthropic's built-in PPTX skill

Skill location: `.claude/skills/pptx-enhanced/`

## CLI User Flow

1. User provides audio file path
2. Audio is transcribed (with progress logging)
3. Content is analyzed and broken down (executive summary, sections, structure)
4. Images are fetched from Unsplash based on identified themes
5. **Preview and Confirmation**: User sees the complete plan and prompt before generation
6. User confirms to proceed with generation
7. PPTX is generated using Claude skill with all context
8. Files are saved: `output/{name}.pptx`, `output/{name}.transcription.json`, `output/{name}.breakdown.json`

## Logging

All modules use structured logging via `utils.get_logger()`. Logs include:
- API call details and cache performance
- File sizes and image dimensions
- Transcription status and timing
- Full prompts sent to Claude (for transparency)
