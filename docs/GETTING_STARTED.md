# Getting Started with Voice-to-Slide

## Quick Start

### 1. Set up your API keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- Get Soniox API key from: https://soniox.com/
- Get Anthropic API key from: https://console.anthropic.com/
- Get Unsplash API key from: https://unsplash.com/developers (optional)

### 2. Verify configuration

```bash
uv run voice-to-slide check
```

### 3. Generate your first presentation

```bash
# Basic usage
uv run voice-to-slide generate your-audio-file.mp3

# Custom output
uv run voice-to-slide generate audio.wav --output my-slides.pptx

# Without images (faster)
uv run voice-to-slide generate audio.mp3 --no-images

# Fast mode (no content enhancement)
uv run voice-to-slide generate audio.mp3 --no-enhance
```

## What You'll Get

1. **Transcription** - Accurate text from your audio (saved as JSON)
2. **Content Analysis** - Claude AI extracts key topics and structure
3. **Professional Slides** - Well-designed PowerPoint presentation
4. **Relevant Images** - Automatically sourced from Unsplash

## Example Workflow

```bash
# Record or prepare your audio file
# meeting-recording.mp3

# Generate presentation
uv run voice-to-slide generate meeting-recording.mp3

# Output:
# - output/meeting-recording.pptx (your presentation)
# - output/meeting-recording.transcription.json (the transcript)
```

## Tips

- **Audio Quality**: Better audio = better transcription
- **Length**: Works best with 2-30 minute recordings
- **Content**: Clear spoken content with distinct topics works best
- **Images**: Enable Unsplash for visually enhanced slides
- **Enhancement**: Use `--enhance` for higher quality (takes longer)

## Troubleshooting

### API Key Issues

Run `uv run voice-to-slide check` to verify all keys are configured.

### Audio Format

Soniox supports: MP3, WAV, M4A, FLAC, OGG and more.

### Rate Limits

- Soniox: Depends on your plan
- Anthropic: Check your API usage dashboard
- Unsplash: 200 requests/hour (free tier)

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [pyproject.toml](pyproject.toml) for dependencies
- Explore the source code in `src/voice_to_slide/`

Enjoy creating presentations from your voice recordings!
