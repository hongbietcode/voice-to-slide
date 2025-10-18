## Product Requirements Document (PRD)

I want to build a voice to slide application that allows users create personalized slide presentations using voice recordings. The application should be able to transcribe voice recordings into text, generate slide content based on the transcribed text, and format the slides in a visually appealing manner.

### Features

1. **Audio To Text Transcription**

    - Users can upload voice recordings in various formats (e.g., MP3, WAV).
    - The application will use speech-to-text technology to transcribe the audio into text.
    - Support for multiple languages and accents.
    - Use **soniox** for high accuracy transcription.

2. **Slide Content Generation**
    - Use claude code sdk to analyze the transcribed text and generate slide content.
    - Automatically create slide titles, bullet points, and key takeaways based on the transcribed text.
    - Allow users to customize the generated content before finalizing the slides.
    - Step generation:
        - Use claude skill **step-generator** to break down the transcribed text into logical sections for slide creation.
        - Use claude skill **document-skills** (https://github.com/anthropics/skills/blob/main/document-skills/pptx/SKILL.md) to create and format the slides based on the generated content.
3. **User Interface**
    - Intuitive and user-friendly interface for uploading audio, reviewing transcriptions, and customizing slides.
    - Real-time preview of slides as they are being generated and formatted.
    - Option to download the final slide presentation in popular formats (e.g., PPTX, PDF).

### Technical Requirements

    -   Command line interface for uploading audio files and generating slides.
    -   Implement audio processing and transcription using Soniox API.
    -   Integrate Claude Code SDK for content generation and slide formatting.
    -   Use uv python for building the backend services.
    -   Research how to get image (main point) from content using claude code sdk.
