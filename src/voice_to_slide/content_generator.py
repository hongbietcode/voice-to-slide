"""Content generation module using Claude Agent SDK."""

import os
import json
from typing import Dict, Any, List
from anthropic import Anthropic
from .utils import get_logger

logger = get_logger(__name__)

class ContentGenerator:
    """Generates slide content from transcribed text using Claude."""

    def __init__(self, api_key: str | None = None, model: str = "claude-haiku-4-5-20251001"):
        """Initialize the content generator with Claude API.

        Args:
            api_key: Anthropic API key. If None, reads from CONTENT_ANTHROPIC_API_KEY env var.
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("CONTENT_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set CONTENT_ANTHROPIC_API_KEY environment variable.")

        # Support custom base URL for API endpoint
        base_url = os.getenv("CONTENT_ANTHROPIC_BASE_URL")
        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            logger.info(f"Using custom Anthropic base URL: {base_url}")

        self.client = Anthropic(**client_kwargs)
        self.model = os.getenv("CONTENT_MODEL", model)
        logger.info(f"ContentGenerator initialized with model: {self.model}")

    def generate_slide_structure(self, transcription_text: str) -> Dict[str, Any]:
        """Generate slide structure from transcribed text.

        Args:
            transcription_text: The transcribed audio text

        Returns:
            Dictionary containing:
                - title: Presentation title
                - slides: List of slide objects with title, content, image_query
        """
        logger.info("Generating slide structure from transcription")

        prompt = f"""Analyze the following transcription and create a structured presentation outline.

TRANSCRIPTION:
{transcription_text}

Please create a presentation structure with:
1. A compelling title for the presentation
2. 5-10 slides that logically organize the content

For each slide, provide:
- title: A clear, concise slide title
- bullet_points: 3-5 key points or takeaways (as a list)
- image_query: A 2-4 word search query for finding a relevant image from Unsplash (e.g., "business meeting", "data analytics", "teamwork collaboration")

Return your response as a valid JSON object with this exact structure:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "title": "Slide Title",
      "bullet_points": ["Point 1", "Point 2", "Point 3"],
      "image_query": "search keywords"
    }}
  ]
}}

Important: Return ONLY the JSON object, no additional text or explanation."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the text content from the response
            response_text = response.content[0].text

            # Parse JSON from response
            # Sometimes Claude wraps JSON in markdown code blocks, so handle that
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            structure = json.loads(response_text)

            logger.info(f"Generated structure with {len(structure.get('slides', []))} slides")
            return structure

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Claude returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    def enhance_slide_content(self, slide: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Enhance a single slide's content with more details.

        Args:
            slide: Slide dictionary with title and bullet_points
            context: Optional context from the full transcription

        Returns:
            Enhanced slide dictionary
        """
        logger.info(f"Enhancing slide: {slide.get('title', 'Untitled')}")

        prompt = f"""Enhance the following slide content to be more engaging and professional.

SLIDE TITLE: {slide.get('title', '')}
CURRENT BULLET POINTS:
{chr(10).join(f"- {point}" for point in slide.get('bullet_points', []))}

{"CONTEXT: " + context[:500] + "..." if context else ""}

Please improve the bullet points to be:
1. More concise and impactful
2. Action-oriented where appropriate
3. Clear and easy to understand
4. Limited to 3-5 points

Return ONLY a JSON array of improved bullet points:
["Improved point 1", "Improved point 2", ...]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text.strip()

            # Extract JSON array
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            enhanced_points = json.loads(response_text)
            slide['bullet_points'] = enhanced_points

            return slide

        except Exception as e:
            logger.warning(f"Failed to enhance slide content: {e}. Using original content.")
            return slide

    def generate_presentation_content(
        self,
        transcription_text: str,
        enhance: bool = False
    ) -> Dict[str, Any]:
        """Generate complete presentation content.

        Args:
            transcription_text: The transcribed audio text
            enhance: Whether to enhance each slide's content (slower but better quality)

        Returns:
            Complete presentation structure
        """
        structure = self.generate_slide_structure(transcription_text)

        if enhance:
            logger.info("Enhancing slide content...")
            enhanced_slides = []
            for slide in structure.get('slides', []):
                enhanced_slide = self.enhance_slide_content(slide, transcription_text[:1000])
                enhanced_slides.append(enhanced_slide)
            structure['slides'] = enhanced_slides

        return structure
