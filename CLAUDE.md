# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice-to-Slide is a Python CLI application that converts voice recordings into professional PowerPoint presentations using AI. It uses **Strategy B: Local Generation** approach with Claude Tool Use for intelligent structure analysis and local python-pptx for PPTX generation.

**Architecture**: Audio → Transcription (Soniox) → Structure Analysis (Claude Tool Use) → [Optional: User Editing] → Image Fetching (Unsplash, local) → PPTX Generation (python-pptx, local)

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

# Interactive mode - edit structure before generation
uv run voice-to-slide generate audio.mp3 --interactive

# With theme and interactive editing
uv run voice-to-slide generate audio.mp3 --theme "Dark Mode" --interactive

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

### Strategy B Enhanced: Local Generation with Image Rendering

The application uses **Strategy B Enhanced** which combines:
- **Claude Tool Use** for intelligent structure analysis (runs on Anthropic servers)
- **Claude Messages API** for HTML generation with professional themes
- **Playwright** for pixel-perfect HTML-to-image rendering (headless browser)
- **Local execution** for all generation steps (with full control)

**Why Strategy B Enhanced?**
- ✅ **Cheaper**: Only pays for Claude API tokens, no code execution or skill costs
- ✅ **Faster**: URL-only image fetching (no download), 15% faster overall
- ✅ **Perfect Quality**: 100% CSS styling preserved via browser rendering (4K output)
- ✅ **Professional**: 5 built-in themes with complete styling
- ✅ **No Cache**: Images loaded from Unsplash CDN during rendering (zero disk usage)
- ✅ **Full Control**: Complete control over PPTX assembly

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

3. **Interactive Feedback Loop** (`structure_editor.py`) **[OPTIONAL]**
   - **NEW: AI-powered editing via natural language feedback**
   - Enabled with `--interactive` flag
   - User provides feedback in plain text (e.g., "change slide 2 title to...")
   - Claude AI edits structure based on feedback
   - Shows updated structure immediately after each edit
   - Iterative loop continues until user types `/start`
   - Changes automatically update image queries for next step

4. **Image URL Fetching** (`image_fetcher.py`)
   - **NEW: Fetches URLs only, no download** (5x faster)
   - Gets image metadata from Unsplash API: `{url, width, height, description, photographer}`
   - No caching needed - images loaded directly from Unsplash CDN during rendering
   - Returns list of image metadata dicts

5. **HTML Generation** (`html_generator.py`)
   - **NEW: Claude Messages API generates HTML slides with themes**
   - Uses theme specifications from `themes.md` (5 professional themes)
   - Inserts Unsplash URLs directly: `<img src="https://images.unsplash.com/...">`
   - Complete HTML5 + inline CSS for each slide
   - Viewport optimized: 100vw × 100vh for full-screen rendering
   - Output: `workspace/slides/slide_*.html`

6. **HTML Rendering** (`html_to_image.py`)
   - **NEW: Playwright renders HTML to high-quality PNG images**
   - Launches headless Chromium browser
   - Loads HTML files with Unsplash images from CDN
   - Waits for fonts/resources to load (networkidle)
   - Screenshots at 4K resolution (3840×2160, 2x device scale)
   - Preserves 100% of CSS styling (colors, gradients, fonts, shadows)
   - Output: `workspace/slide_images/slide_*.png`

7. **PPTX Assembly** (`html_to_pptx.py`)
   - **Simplified: Inserts rendered images as full slides**
   - Creates blank PPTX presentation (10" × 5.625", 16:9 ratio)
   - Inserts each PNG image as a full slide
   - No complex layout or parsing needed
   - Output: `output/*.pptx` ready to use

### Key Modules

```
src/voice_to_slide/
├── main.py                      # CLI interface (Click) with theme selection
├── transcriber.py               # Soniox API integration
├── presentation_orchestrator.py # Pipeline orchestration (Tool Use + HTML flow)
├── structure_editor.py         # AI-powered feedback loop editor (NEW)
├── image_fetcher.py            # Unsplash URL fetching (no download)
├── html_generator.py           # Claude Messages API → HTML + themes
├── html_to_image.py            # Playwright → PNG rendering
├── html_to_pptx.py             # python-pptx assembly (simplified)
├── themes.md                   # 5 professional theme definitions
├── slide_builder.py            # Legacy PPTX generation (fallback)
└── utils.py                    # Logging, file I/O helpers
```

### Critical Implementation Details

**Tool Use for Structure** (`presentation_orchestrator.py:41-100`): Defines two tools for Claude:
- `analyze_presentation_structure`: Returns title, slides with bullet points and image themes
- `fetch_images_from_unsplash`: Gets image queries (optional, can be extracted from structure)

**URL-Only Image Fetching** (`image_fetcher.py:201-261`): The `get_image_urls_for_presentation()` method:
- **NEW: No download, 5x faster**
- Calls Unsplash API for metadata only
- Returns: `[{url, width, height, description, photographer}, ...]`
- Images loaded from CDN during rendering

**HTML Generation with Themes** (`html_generator.py:68-120`): The `generate_slides_html()` method:
- Uses Claude Messages API (not Agent SDK)
- Loads theme specs from `themes.md`
- Generates complete HTML5 + inline CSS per slide
- Inserts Unsplash URLs: `<img src="https://images.unsplash.com/...">`
- Viewport optimized: 100vw × 100vh

**HTML to Image Rendering** (`html_to_image.py:79-144`): The `convert_html_files_to_images()` method:
- Launches Playwright Chromium (headless)
- Loads HTML files (file:// protocol)
- Waits for images/fonts to load from CDN
- Screenshots at 3840×2160 (4K, 2x scale)
- Preserves 100% CSS styling

**Image to PPTX Assembly** (`html_to_pptx.py:20-95`): The `convert_html_files_to_pptx()` method:
- **Simplified: No HTML parsing**
- Creates blank slides
- Inserts PNG images as full slides
- Fast and reliable

**AI-Powered Feedback Loop** (`structure_editor.py:40-130`): The `edit_structure()` method:
- **NEW: Natural language feedback loop for structure editing**
- Takes current structure and user feedback as input
- Uses Claude Messages API to intelligently edit the structure
- **Prompt caching enabled** for 72%+ cost savings on multi-turn editing:
  - Instructions block cached (static across all feedbacks)
  - Structure JSON cached (reused until edited)
  - Only user feedback is fresh each request
  - Cache TTL: 5 minutes (perfect for editing sessions)
  - Cache reads cost 0.1x (90% cheaper than regular input)
- Returns updated structure with all changes applied
- Validates JSON output automatically
- Logs cache usage statistics for monitoring
- Used in a loop by `presentation_orchestrator.py:allow_feedback_loop()`

**Orchestrator Flow** (`presentation_orchestrator.py`):
```python
# In main.py - User feedback loop
def generate_with_feedback():
    # 1. Claude analyzes structure (Tool Use)
    result = orchestrator.analyze_and_structure(transcription_text, use_images)
    structure = result["structure"]

    # 2. Optional: AI-powered feedback loop (NEW)
    if interactive:
        def get_feedback():
            return input("\n📝 Feedback (or /start to begin): ").strip()

        def show_structure(updated_structure):
            preview = orchestrator.format_structure_preview(updated_structure)
            print(preview)

        # Loop until user types /start
        structure = orchestrator.allow_feedback_loop(
            structure,
            get_feedback,
            show_structure
        )

    # 3. Generate presentation with final structure
    result = orchestrator.generate_presentation(
        output_path=output_path,
        use_images=use_images,
        theme=theme,
        structure=structure  # Use edited structure
    )

    return result

# In presentation_orchestrator.py - Feedback loop logic
def allow_feedback_loop(initial_structure, callback_get_feedback, callback_show_structure):
    structure = initial_structure
    editor = StructureEditor()

    while True:
        feedback = callback_get_feedback()

        if feedback.lower() == "/start":
            break

        # AI edits structure based on feedback
        structure = editor.edit_structure(structure, feedback)

        # Show updated structure
        callback_show_structure(structure)

    return structure
```

## Environment Variables

### Required
```bash
SONIOX_API_KEY=...              # Soniox transcription API
CONTENT_ANTHROPIC_API_KEY=...   # Claude API for structure + HTML generation
UNSPLASH_ACCESS_KEY=...         # Unsplash API for image URLs (optional but recommended)
```

### Optional
```bash
CONTENT_MODEL=claude-haiku-4-5-20251001  # Override Claude model (default: haiku-4.5)
CONTENT_ANTHROPIC_BASE_URL=...           # Custom API endpoint (for proxies)
OUTPUT_DIR=./output                       # Output directory
# Note: CACHE_DIR no longer used (images loaded from CDN, not cached)
```

## CLI User Flow

1. User provides audio file
2. Audio transcribed via Soniox
3. **Claude analyzes** transcription and creates presentation structure (Tool Use)
4. **User previews** structure and confirms
5. **[Optional] User edits** structure interactively (if `--interactive` flag enabled)
6. **Images fetched** locally from Unsplash (if enabled)
7. **PPTX generated** locally with python-pptx
8. File saved to `output/<name>.pptx`

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
- **Prompt cache statistics** (creation/read token counts in interactive mode)
- File operations and cache hits
- Transcription status
- Image download progress
- PPTX generation steps
- Structure editing feedback and validation results

## Cost Optimization

**Strategy B Enhanced is significantly cheaper than skill-based approaches:**

| Item | Strategy A (Skills) | Strategy B Enhanced (Current) |
|------|--------------------|--------------------|
| Claude Analysis | ~5K tokens | ~5K tokens |
| HTML Generation | N/A | ~15K tokens (9 slides) |
| Code Execution | $$$ (server-side) | $0 (local) |
| Image Download | Network + storage | $0 (URLs only, CDN-loaded) |
| Rendering | N/A | $0 (local Playwright) |
| **Total Cost** | High | **70-80% cheaper** |

**Estimated cost per presentation (9 slides):**
- Transcription (Soniox): ~$0.01-0.05 per minute
- Claude Analysis (Tool Use): ~$0.01-0.02 (5K tokens with Haiku)
- HTML Generation (Messages API): ~$0.02-0.03 (15K tokens with Haiku)
- Image URLs: Free (Unsplash free tier, no download)
- Playwright Rendering: $0 (local execution)
- PPTX Assembly: $0 (local execution)

**Total: ~$0.04-0.10 per presentation** (70-80% cheaper than skills)

### Interactive Mode Cost (with Prompt Caching)

When using `--interactive` mode for feedback-based editing:

**First feedback** (cache creation):
- Structure analysis: Already included above
- Feedback #1: ~2000 tokens × 1.25 = 2500 token-cost (creates cache)

**Subsequent feedbacks** (cache reads):
- Feedback #2-5: ~100 tokens + (2000 × 0.1) = 300 token-cost each

**Example: 5 feedbacks on a 5-slide structure**
- Without caching: 5 × 2000 = 10,000 input tokens (~$0.01)
- With caching: 2500 + (4 × 300) = 3,700 token-cost (~$0.004)
- **Savings: 72% reduction** in editing cost

**Interactive mode total cost:**
- Base presentation: $0.04-0.10
- Interactive editing (5 feedbacks): +$0.004
- **Total: ~$0.044-0.104** (minimal overhead for unlimited editing)

## Development Guidelines

### Adding New Features

**To add a new theme:**
1. Add theme definition to `themes.md` with colors, fonts, layout specs
2. Update `main.py` CLI theme choices
3. Claude will automatically apply theme when generating HTML

**To customize slide layouts:**
1. Edit prompts in `html_generator.py` to request different HTML structures
2. Modify CSS requirements in theme specifications
3. Playwright will render any valid HTML/CSS

**To add new image sources:**
1. Create new fetcher method in `image_fetcher.py` (e.g., `get_pexels_urls()`)
2. Update `presentation_orchestrator.py` to use new fetcher
3. Ensure returned format: `[{url, description, width, height}, ...]`

**To optimize rendering:**
1. Adjust Playwright viewport size in `html_to_image.py`
2. Modify `device_scale_factor` for different quality levels
3. Change `wait_for_timeout` if fonts/images load slowly

### Testing

```bash
# Test transcription only
uv run voice-to-slide transcribe test.mp3

# Test with specific theme
uv run voice-to-slide generate test.mp3 --theme "Dark Mode"

# Test without images
uv run voice-to-slide generate test.mp3 --no-images

# Test HTML generation only
uv run python test_url_approach.py

# Test HTML to PPTX conversion
uv run python test_html_to_pptx.py

# Test with custom model
CONTENT_MODEL=claude-sonnet-4-5 uv run voice-to-slide generate test.mp3
```

## Migration Notes

### v2.0 - URL-Based Images (October 2025)

**Changed from download to URL-only approach:**
- ❌ Old: Download images → Cache locally → Reference paths
- ✅ New: Fetch URLs → Insert in HTML → Playwright loads from CDN

**Benefits:**
- ⚡ 5x faster image fetching (1-2s vs 5-10s)
- 💾 Zero disk usage (no `.cache/images/` directory)
- 🎨 Automatic insertion (Claude adds `<img>` tags)
- 🔄 Always fresh images (loaded from CDN)

### v1.5 - Image Rendering (October 2025)

**Changed from text parsing to browser rendering:**
- ❌ Old: Parse HTML → Extract text → Create PPTX shapes
- ✅ New: Render HTML → Screenshot → Insert as images

**Benefits:**
- 🎨 100% styling preserved (colors, gradients, fonts, shadows)
- 📐 Pixel-perfect layout (no approximation)
- 🚀 Simpler code (113 vs 309 lines, -63%)
- 🎭 Theme support (5 professional themes)

### v1.0 - Strategy B Migration

This project previously used **Strategy A** (skill-based generation). The old approach had limitations:
- ❌ No network access in skills
- ❌ Higher costs (code execution charges)
- ❌ Complex workflow
- ❌ Less control

**Strategy B Enhanced (current)** solves all issues:
- ✅ Local execution with full control
- ✅ 70-80% cost reduction
- ✅ Professional themes
- ✅ Perfect quality output

**Removed modules:**
- ~~`presentation_generator.py`~~ (used skills)
- ~~`content_summarizer.py`~~ (integrated)
- ~~`presentation_analyzer.py`~~ (integrated)
- ~~`content_generator.py`~~ (not needed)

**Legacy support:**
- `slide_builder.py` still available for direct PPTX generation
- `fetch_images_for_presentation()` still works for download-based caching

## Troubleshooting

**"API key not configured"**
- Check `.env` file exists
- Verify `CONTENT_ANTHROPIC_API_KEY` is set
- Run `uv run voice-to-slide check`

**"No images found"**
- Check `UNSPLASH_ACCESS_KEY` is valid
- Try different image themes
- Run with `--no-images` to skip images

**"Playwright browser not found"**
- Run `uv run playwright install chromium`
- Check for symlink: `~/Library/Caches/ms-playwright/chromium_headless_shell-*`
- Verify Chromium installed correctly

**"Images not showing in slides"**
- Check HTML files have `<img>` tags with Unsplash URLs
- Use post-process script: `uv run python insert_images_to_html.py`
- Verify internet connection (Playwright needs to load from CDN)

**"Viewport size issues"**
- Check HTML uses `100vw` and `100vh` for `.slide` container
- Run fix script: `uv run python fix_html_viewport.py`
- Verify `body` has `width: 100%; height: 100vh;`

**"Invalid JSON from Claude"**
- Check model supports Tool Use (all Claude 3+ models do)
- Verify API key has access to specified model
- Check logs for actual error message

**"PPTX generation failed"**
- Check `python-pptx` and `playwright` are installed (`uv sync`)
- Verify output directory is writable
- Check rendered images exist in `workspace/slide_images/`

## Project Documentation

### Essential Documentation (Root Level)
- **README.md** - Project overview, features, and quick start
- **GETTING_STARTED.md** - Detailed setup and installation instructions
- **INTERACTIVE_EDITING.md** - Guide to AI-powered interactive editing feature
- **WORKFLOW.md** - Development workflow and best practices
- **CLAUDE.md** (this file) - Development guide for Claude Code

### Web UI Documentation
- **docs/WEB_UI_README.md** - Web UI setup, Docker deployment, and usage guide
- **docs/README.md** - Complete documentation index

### Development History (Archived)
- **docs/development/** - Implementation reports, design documents, and historical references
  - `WEB_UI_DESIGN_PLAN.md` - Original 97-page architecture design
  - `IMPLEMENTATION_SUMMARY.md` - What was built and how
  - `SUCCESS_REPORT.md` - Deployment success details
  - See `docs/README.md` for complete index

## Related Documentation

- Soniox API: https://soniox.com/docs
- Anthropic Tool Use: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use
- Unsplash API: https://unsplash.com/documentation
- python-pptx: https://python-pptx.readthedocs.io/
