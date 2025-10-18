# Voice-to-Slide

Convert voice recordings into professional PowerPoint presentations automatically using AI.

## Features

- **Audio Transcription**: High-accuracy speech-to-text using Soniox API
- **AI-Powered Content Generation**: Claude AI analyzes transcripts and generates structured slide content
- **Professional Slide Design**: Automatic slide creation using Claude's PPTX skill
- **Image Integration**: Relevant images from Unsplash API
- **Fast CLI Interface**: Simple command-line tool built with Click
- **Modern Python**: Built with uv for blazing-fast dependency management

## Prerequisites

- Python 3.10 or higher
- Node.js (required for Claude PPTX skill)
- API keys for:
  - Soniox (audio transcription)
  - Anthropic (Claude AI)
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

Edit `.env` and add your API keys.

**Optional**: Set `ANTHROPIC_BASE_URL` if using a custom API endpoint or proxy.

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
1. Transcribe the audio file
2. Analyze the content
3. Fetch relevant images (if Unsplash is configured)
4. Generate a professional PPTX presentation
5. Save to `./output/recording.pptx`

### Advanced options

```bash
# Specify custom output path
uv run voice-to-slide generate audio.wav --output my-presentation.pptx

# Disable image fetching
uv run voice-to-slide generate audio.mp3 --no-images

# Disable content enhancement (faster)
uv run voice-to-slide generate audio.mp3 --no-enhance
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
2. **Analysis**: Claude analyzes the transcript and identifies key topics
3. **Image Sourcing**: Unsplash API fetches relevant images
4. **Slide Generation**: Claude's PPTX skill creates the presentation
5. **Output**: A polished PowerPoint file ready to use

## Project Structure

```
voice-to-slide/
├── src/voice_to_slide/
│   ├── main.py                    # CLI interface
│   ├── transcriber.py             # Soniox integration
│   ├── presentation_generator.py  # Claude PPTX skill integration
│   ├── image_fetcher.py           # Unsplash integration
│   └── utils.py                   # Helper functions
├── output/                        # Generated presentations
├── pyproject.toml                 # Project configuration
└── .env                           # API keys (gitignored)
```

## License

MIT License
