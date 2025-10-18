# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice-to-Slide is a Python CLI application that converts voice recordings into professional PowerPoint presentations using AI. It uses **Strategy B: Local Generation** approach with Claude Tool Use for intelligent structure analysis and local python-pptx for PPTX generation.

**Architecture**: Audio → Transcription (Soniox) → Structure Analysis (Claude Tool Use) → Image Fetching (Unsplash, local) → PPTX Generation (python-pptx, local)

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
# Edit .env to add: SONIOX_API_KEY, CONTENT_ANTHROPIC_API_KEY, UNSPLASH_ACCESS_KEY

# Verify configuration
uv run voice-to-slide check
```

### Running the Application
```bash
# Generate presentation from audio
uv run voice-to-slide generate <audio-file>

# With options
uv run voice-to-slide generate audio.mp3 --output slides.pptx --no-images

# Transcribe only
uv run voice-to-slide transcribe audio.mp3

# Check API configuration
uv run voice-to-slide check
```

### Testing and Development
```bash
# Run the CLI directly during development
uv run python -m voice_to_slide.main generate recording.mp3

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

### Strategy B: Local Generation with Tool Use

The application uses **Strategy B** which combines:
- **Claude Tool Use** for intelligent analysis (runs on Anthropic servers)
- **Local execution** for image fetching (with network access) and PPTX generation (with full control)

**Why Strategy B?**
- ✅ **Cheaper**: Only pays for Claude analysis tokens, no code execution costs
- ✅ **Faster**: No upload/download overhead for images and PPTX files
- ✅ **Network Access**: Can fetch images from Unsplash API during generation
- ✅ **Full Control**: Complete control over PPTX layout and styling with python-pptx

### Pipeline Flow

1. **Audio Transcription** (`transcriber.py`)
   - Uses Soniox API for high-accuracy speech-to-text
   - Handles both sync (<10MB) and async transcription automatically
   - Outputs: transcription text + word-level timestamps

2. **Structure Analysis** (`presentation_orchestrator.py`)
   - Uses **Claude Tool Use** with 2 tools:
     - `analyze_presentation_structure`: Analyzes transcription and creates slide structure
     - `fetch_images_from_unsplash`: Suggests image queries for each slide
   - Claude decides structure, bullet points, and image themes
   - Returns structured JSON with presentation plan

3. **Image Fetching** (`image_fetcher.py`)
   - **Runs locally with full network access**
   - Fetches images from Unsplash API based on themes from Claude
   - Downloads and caches in `.cache/images/`
   - Resizes to max 1920x1080 for optimal file size
   - Naming: `slide_00_*.jpg`, `slide_01_*.jpg`, etc.

4. **PPTX Generation** (`slide_builder.py`)
   - **Runs locally with python-pptx library**
   - Full control over slide layout, fonts, colors
   - Adds images directly from local cache
   - No upload/download to Anthropic servers
   - Generates `.pptx` file ready to use

### Key Modules

```
src/voice_to_slide/
├── main.py                      # CLI interface (Click)
├── transcriber.py               # Soniox API integration
├── presentation_orchestrator.py # Claude Tool Use orchestration (NEW)
├── image_fetcher.py            # Unsplash API with local caching
├── slide_builder.py            # python-pptx PPTX generation
└── utils.py                    # Logging, file I/O helpers
```

### Critical Implementation Details

**Tool Use for Structure** (`presentation_orchestrator.py:41-100`): Defines two tools for Claude:
- `analyze_presentation_structure`: Returns title, slides with bullet points and image themes
- `fetch_images_from_unsplash`: Gets image queries (optional, can be extracted from structure)

**Local Image Fetching** (`image_fetcher.py:123-164`): The `fetch_images_for_presentation()` method:
- Runs on your machine with full network access
- Calls Unsplash API for each image query
- Downloads and caches locally
- Returns list of file paths

**Local PPTX Building** (`slide_builder.py:164-186`): The `build_presentation()` method:
- Takes structure dict and image paths
- Creates slides using python-pptx API
- Full control over layout (title, bullets, images)
- No dependency on external services

**Orchestrator Flow** (`presentation_orchestrator.py:191-236`):
```python
def generate_presentation(transcription_text, output_path, use_images):
    # 1. Claude analyzes structure (Tool Use)
    result = analyze_and_structure(transcription_text, use_images)
    structure = result["structure"]
    image_queries = result["image_queries"]
    
    # 2. Fetch images locally (network access)
    image_paths = fetch_images(image_queries)
    
    # 3. Build PPTX locally (python-pptx)
    output_path = SlideBuilder.create_presentation(
        content=structure,
        output_path=output_path,
        image_paths=image_paths
    )
    
    return {"status": "success", "output_path": output_path}
```

## Environment Variables

### Required
```bash
SONIOX_API_KEY=...              # Soniox transcription API
CONTENT_ANTHROPIC_API_KEY=...   # Claude API for structure analysis
UNSPLASH_ACCESS_KEY=...         # Unsplash API for images (optional but recommended)
```

### Optional
```bash
CONTENT_MODEL=claude-haiku-4-5-20251001  # Override Claude model (default: haiku-4.5)
CONTENT_ANTHROPIC_BASE_URL=...           # Custom API endpoint (for proxies)
OUTPUT_DIR=./output                       # Output directory
CACHE_DIR=./.cache                        # Image cache directory
```

## CLI User Flow

1. User provides audio file
2. Audio transcribed via Soniox
3. **Claude analyzes** transcription and creates presentation structure (Tool Use)
4. **User previews** structure and confirms
5. **Images fetched** locally from Unsplash (if enabled)
6. **PPTX generated** locally with python-pptx
7. File saved to `output/<name>.pptx`

**Output Example:**
```
🎙️  Voice-to-Slide Generator
==================================================
Audio file: recording.mp3

📝 Step 1: Transcribing audio...
   Transcribed 5234 characters

🧠 Step 2: Analyzing content and generating structure...
======================================================================
PRESENTATION PREVIEW
======================================================================

Title: Your Presentation Title
Total Slides: 6 (including title slide)

Slide 2: Introduction
  Image: business meeting
  Points:
    • First key point
    • Second key point
    
...

⚠️  Proceed with presentation generation? [Y/n]: Y

🎨 Step 3: Generating presentation (Strategy B: Local Generation)...
   • Using Claude Tool Use for structure analysis
   • Fetching images locally with network access
   • Building PPTX locally with python-pptx

✅ Success! Presentation generated:
   📄 File: output/recording.pptx
   📊 Total slides: 6
   🖼️  Images: 5/5
```

## Logging

All modules use structured logging via `utils.get_logger()`. Logs include:
- API call details and response summaries
- File operations and cache hits
- Transcription status
- Image download progress
- PPTX generation steps

## Cost Optimization

**Strategy B is significantly cheaper than skill-based approaches:**

| Item | Strategy A (Skills) | Strategy B (Local) |
|------|--------------------|--------------------|
| Claude Analysis | ~5K tokens | ~5K tokens |
| Code Execution | $$$ (server-side) | $0 (local) |
| Image Upload/Download | Network overhead | $0 (local) |
| **Total Cost** | High | **70-80% cheaper** |

**Estimated cost per presentation:**
- Transcription (Soniox): ~$0.01-0.05 per minute
- Claude Analysis: ~$0.01-0.02 (5K tokens with Haiku)
- Images: Free (Unsplash free tier)
- PPTX Generation: $0 (local)

**Total: ~$0.02-0.07 per presentation** (mostly transcription)

## Development Guidelines

### Adding New Features

**To add a new slide layout:**
1. Add method to `slide_builder.py` (e.g., `add_two_column_slide()`)
2. Update tool schema in `presentation_orchestrator.py` if needed
3. Claude will automatically use new layout based on updated schema

**To customize styling:**
1. Edit color constants in `slide_builder.py` (TITLE_COLOR, etc.)
2. Modify font sizes in slide creation methods
3. No need to update Claude - styling is purely local

**To support new image sources:**
1. Create new fetcher class (e.g., `PexelsFetcher`)
2. Update `presentation_orchestrator.py` to use new fetcher
3. Update tool descriptions if needed

### Testing

```bash
# Test transcription only
uv run voice-to-slide transcribe test.mp3

# Test with preview (stops before generation)
# Modify main.py to return after preview

# Test with custom model
CONTENT_MODEL=claude-sonnet-4-5 uv run voice-to-slide generate test.mp3

# Test without images
uv run voice-to-slide generate test.mp3 --no-images
```

## Migration Notes

This project previously used **Strategy A** (skill-based generation with code execution on Anthropic servers). The old approach had limitations:
- ❌ No network access in skills (couldn't fetch images)
- ❌ Higher costs (code execution charges)
- ❌ Complex upload/download workflow
- ❌ Less control over PPTX layout

**Strategy B (current)** solves all these issues by running image fetching and PPTX generation locally, while using Claude only for intelligent structure analysis via Tool Use.

Old modules have been removed:
- ~~`presentation_generator.py`~~ (used skills)
- ~~`content_summarizer.py`~~ (integrated into orchestrator)
- ~~`presentation_analyzer.py`~~ (integrated into orchestrator)
- ~~`content_generator.py`~~ (not needed)

## Troubleshooting

**"API key not configured"**
- Check `.env` file exists
- Verify `CONTENT_ANTHROPIC_API_KEY` is set
- Run `uv run voice-to-slide check`

**"No images found"**
- Check `UNSPLASH_ACCESS_KEY` is valid
- Try different image themes
- Run with `--no-images` to skip images

**"Invalid JSON from Claude"**
- Check model supports Tool Use (all Claude 3+ models do)
- Verify API key has access to specified model
- Check logs for actual error message

**"PPTX generation failed"**
- Check `python-pptx` is installed (`uv sync`)
- Verify output directory is writable
- Check image files exist in cache

## Related Documentation

- Soniox API: https://soniox.com/docs
- Anthropic Tool Use: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use
- Unsplash API: https://unsplash.com/documentation
- python-pptx: https://python-pptx.readthedocs.io/
