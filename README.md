# Voice-to-Slide

Convert voice recordings into professional PowerPoint presentations automatically using AI.

## Features

- **Audio Transcription**: High-accuracy speech-to-text using Soniox API
- **AI-Powered Structure Analysis**: Claude AI analyzes transcripts and creates presentation structure using Tool Use
- **Local PPTX Generation**: Professional slide creation using python-pptx with full control
- **Image Integration**: Relevant images from Unsplash API fetched locally with network access
- **Fast & Cost-Effective**: Local generation is 70-80% cheaper than cloud-based approaches
- **Simple CLI**: Easy-to-use command-line tool built with Click
- **Modern Python**: Built with uv for blazing-fast dependency management

## Architecture

Uses **Strategy B: Local Generation**
- Claude Tool Use for intelligent structure analysis (cloud)
- Local image fetching with full network access
- Local PPTX generation with python-pptx (no upload/download overhead)

## Prerequisites

- Python 3.10 or higher
- API keys for:
  - Soniox (audio transcription)
  - Anthropic Claude (structure analysis)
  - Unsplash (optional, for images)

## Installation

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure API keys

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
SONIOX_API_KEY=your_soniox_key
CONTENT_ANTHROPIC_API_KEY=your_claude_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
```

**Optional**: Set `CONTENT_ANTHROPIC_BASE_URL` if using a custom API endpoint or proxy.

### 3. Verify setup

```bash
uv run voice-to-slide check
```

## Usage

### Generate a presentation from audio

```bash
uv run voice-to-slide generate recording.mp3
```

This will:
1. Transcribe the audio file using Soniox
2. Analyze content and create structure using Claude Tool Use
3. Preview the presentation plan and ask for confirmation
4. Fetch relevant images locally from Unsplash (if configured)
5. Generate PPTX file locally using python-pptx
6. Save to `./output/recording.pptx`

### Advanced options

```bash
# Specify custom output path
uv run voice-to-slide generate audio.wav --output my-presentation.pptx

# Disable image fetching
uv run voice-to-slide generate audio.mp3 --no-images
```

### Transcribe audio only

```bash
uv run voice-to-slide transcribe recording.mp3
```

### Check configuration

```bash
uv run voice-to-slide check
```

## How It Works

1. **Transcription**: Soniox converts audio to text with high accuracy
2. **Structure Analysis**: Claude uses Tool Use to analyze transcript and create presentation structure
3. **Preview & Confirm**: User reviews the proposed structure before generation
4. **Image Fetching**: Unsplash API fetches relevant images locally (with network access)
5. **PPTX Generation**: python-pptx creates the presentation locally (full control over layout)
6. **Output**: A polished PowerPoint file ready to use

## Why This Approach?

**Strategy B: Local Generation with Tool Use**
- ✅ **Cost-Effective**: 70-80% cheaper than cloud code execution approaches
- ✅ **Fast**: No upload/download overhead for images and PPTX files
- ✅ **Network Access**: Can fetch images from external APIs during generation
- ✅ **Full Control**: Complete control over PPTX layout and styling
- ✅ **Transparent**: Preview structure before generation

## Project Structure

```
voice-to-slide/
├── src/voice_to_slide/
│   ├── main.py                      # CLI interface
│   ├── transcriber.py               # Soniox integration
│   ├── presentation_orchestrator.py # Claude Tool Use orchestration
│   ├── image_fetcher.py             # Unsplash integration (local)
│   ├── slide_builder.py             # python-pptx generation (local)
│   └── utils.py                     # Helper functions
├── output/                          # Generated presentations
├── .cache/images/                   # Cached images from Unsplash
├── pyproject.toml                   # Project configuration
└── .env                             # API keys (gitignored)
```

## License

MIT License
