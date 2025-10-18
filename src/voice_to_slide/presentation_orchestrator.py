"""Presentation orchestration using Claude Tool Use (Strategy B: Local Generation)."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from .utils import get_logger
from .image_fetcher import ImageFetcher
from .slide_builder import SlideBuilder
from .html_generator import HTMLSlideGenerator
from .html_to_pptx import convert_html_to_pptx

logger = get_logger(__name__)


class PresentationOrchestrator:
    """Orchestrates presentation generation using Claude Tool Use and local execution."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the orchestrator.

        Args:
            api_key: Anthropic API key. If None, reads from CONTENT_ANTHROPIC_API_KEY env var.
            model: Claude model to use. If None, reads from CONTENT_MODEL env var (default: claude-haiku-4-5-20251001)
        """
        self.api_key = api_key or os.getenv("CONTENT_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set CONTENT_ANTHROPIC_API_KEY."
            )

        # Get model from env or use default
        self.model = model or os.getenv("CONTENT_MODEL", "claude-haiku-4-5-20251001")

        # Setup client with optional custom base URL and prompt caching
        base_url = os.getenv("CONTENT_ANTHROPIC_BASE_URL")
        client_kwargs = {
            "api_key": self.api_key,
            "default_headers": {
                "anthropic-beta": "prompt-caching-2024-07-31"
            }
        }
        if base_url:
            client_kwargs["base_url"] = base_url
            logger.info(f"Using custom base URL: {base_url}")

        self.client = Anthropic(**client_kwargs)
        logger.info("Prompt caching enabled")
        
        logger.info(f"PresentationOrchestrator initialized with model: {self.model}")

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for Claude.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "analyze_presentation_structure",
                "description": """Analyze transcription and determine presentation structure.
                
                This tool should extract:
                - Main title for the presentation
                - List of slides with titles and key bullet points
                - Suggested image themes for each slide (if applicable)
                
                Create a clear, logical flow with:
                - Opening slide with main topic
                - 3-7 content slides covering key points
                - Optional closing slide with conclusions/takeaways
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Main presentation title"
                        },
                        "slides": {
                            "type": "array",
                            "description": "List of content slides",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Slide title"
                                    },
                                    "bullet_points": {
                                        "type": "array",
                                        "description": "Key points for this slide (3-5 points)",
                                        "items": {"type": "string"}
                                    },
                                    "image_theme": {
                                        "type": "string",
                                        "description": "Optional image search query for this slide (e.g., 'business meeting', 'data analytics')"
                                    }
                                },
                                "required": ["title", "bullet_points"]
                            }
                        }
                    },
                    "required": ["title", "slides"]
                }
            },
            {
                "name": "fetch_images_from_unsplash",
                "description": """Fetch images from Unsplash API based on search queries.
                
                Use this tool to get relevant images for presentation slides.
                Each query should be descriptive (e.g., 'modern office workspace', 
                'data visualization charts', 'team collaboration').
                
                Images will be downloaded and cached locally for use in the presentation.
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "description": "List of search queries for images",
                            "items": {
                                "type": "string",
                                "description": "Image search query"
                            }
                        }
                    },
                    "required": ["queries"]
                }
            }
        ]

    def analyze_and_structure(
        self,
        transcription_text: str,
        use_images: bool = True
    ) -> Dict[str, Any]:
        """Analyze transcription and get presentation structure using Tool Use.

        Args:
            transcription_text: Transcribed audio text
            use_images: Whether to suggest images for slides

        Returns:
            Dictionary with structure and image queries
        """
        logger.info("Analyzing transcription with Claude Tool Use")

        # Build prompt
        prompt = f"""Analyze this transcription and create a professional presentation structure.

Transcription:
{transcription_text}

Instructions:
1. Extract the main topic and create a compelling title
2. Organize content into 4-8 logical slides
3. For each slide, create 3-5 clear, concise bullet points
4. {"Suggest relevant image themes for each slide" if use_images else "Focus on text content only"}
5. Ensure the presentation flows logically from introduction to conclusion

Use the analyze_presentation_structure tool to provide the complete structure.
{"Then use fetch_images_from_unsplash to get images for each slide." if use_images else ""}"""

        # Initial request with tool definitions
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            tools=self._get_tool_definitions(),
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        logger.info(f"Claude response - stop_reason: {response.stop_reason}")

        # Extract tool uses
        structure = None
        image_queries = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                logger.info(f"Tool used: {content_block.name}")
                
                if content_block.name == "analyze_presentation_structure":
                    structure = content_block.input
                    logger.info(f"Structure received: {structure['title']}, {len(structure['slides'])} slides")
                
                elif content_block.name == "fetch_images_from_unsplash":
                    image_queries = content_block.input.get("queries", [])
                    logger.info(f"Image queries received: {len(image_queries)} queries")

        if not structure:
            raise ValueError("Claude did not provide presentation structure")

        # Extract image themes from slides if not provided via tool
        if use_images and not image_queries:
            image_queries = []
            for slide in structure.get("slides", []):
                theme = slide.get("image_theme", "")
                if theme:
                    image_queries.append(theme)

        return {
            "structure": structure,
            "image_queries": image_queries if use_images else []
        }

    def fetch_images(self, image_queries: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Fetch image URLs using ImageFetcher (no download, just URLs).

        Args:
            image_queries: List of search queries

        Returns:
            List of image metadata dicts {url, width, height, description} (None for failed queries)
        """
        if not image_queries:
            logger.info("No image queries provided, skipping image fetch")
            return []

        logger.info(f"Fetching {len(image_queries)} image URLs from Unsplash")

        try:
            fetcher = ImageFetcher()
            image_data = fetcher.get_image_urls_for_presentation(image_queries)
            successful = sum(1 for p in image_data if p is not None)
            logger.info(f"Successfully fetched {successful}/{len(image_queries)} image URLs")
            return image_data
        except ValueError as e:
            logger.error(f"Failed to fetch image URLs: {e}")
            return [None] * len(image_queries)

    def generate_presentation(
        self,
        transcription_text: str,
        output_path: Path | str,
        use_images: bool = True,
        theme: str = "Modern Professional",
        use_html_generation: bool = True
    ) -> Dict[str, Any]:
        """Generate complete presentation using Tool Use + local execution.

        Args:
            transcription_text: Transcribed audio text
            output_path: Path to save PPTX file
            use_images: Whether to include images
            theme: Theme name for styling (from themes.md)
            use_html_generation: Use Agent SDK HTML generation (recommended)

        Returns:
            Result dictionary with status and file info
        """
        logger.info(f"Starting presentation generation (Strategy B with {'HTML' if use_html_generation else 'direct'} generation)")

        try:
            # Step 1: Analyze and structure using Claude Tool Use
            result = self.analyze_and_structure(transcription_text, use_images)
            structure = result["structure"]
            image_queries = result["image_queries"]

            # Step 2: Fetch image URLs (no download, just metadata)
            image_data = []
            if use_images and image_queries:
                image_data = self.fetch_images(image_queries)

            # Step 3: Generate presentation
            if use_html_generation:
                # NEW FLOW: HTML Generation → PPTX Conversion
                logger.info(f"Generating HTML slides with theme: {theme}")

                # Step 3a: Generate HTML slides using Messages API
                base_url = os.getenv("CONTENT_ANTHROPIC_BASE_URL")
                html_generator = HTMLSlideGenerator(
                    api_key=self.api_key,
                    model=self.model,
                    base_url=base_url
                )

                html_files = html_generator.generate_slides_html(
                    structure=structure,
                    image_data=image_data,
                    theme=theme
                )

                logger.info(f"Generated {len(html_files)} HTML files")

                # Step 3b: Convert HTML → Images → PPTX
                logger.info("Converting HTML slides to PPTX (via images)")
                output_path = convert_html_to_pptx(
                    html_files=html_files,
                    output_path=Path(output_path),
                    image_dir=None  # Auto-generate in output dir
                )

                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "structure": structure,
                    "images_fetched": len([p for p in image_data if p is not None]),
                    "total_slides": len(structure.get("slides", [])) + 1,
                    "theme": theme,
                    "html_files": [str(f) for f in html_files]
                }

            else:
                # OLD FLOW: Direct PPTX generation
                logger.info("Generating PPTX file directly")
                output_path = SlideBuilder.create_presentation(
                    content=structure,
                    output_path=output_path,
                    image_paths=image_paths if image_paths else None
                )

                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "structure": structure,
                    "images_fetched": len([p for p in image_paths if p is not None]),
                    "total_slides": len(structure.get("slides", [])) + 1
                }

        except Exception as e:
            logger.exception("Presentation generation failed")
            return {
                "status": "error",
                "error": str(e)
            }

    def preview_structure(
        self,
        transcription_text: str,
        use_images: bool = True
    ) -> str:
        """Preview presentation structure without generating file.

        Args:
            transcription_text: Transcribed audio text
            use_images: Whether to suggest images

        Returns:
            Formatted preview string
        """
        result = self.analyze_and_structure(transcription_text, use_images)
        structure = result["structure"]
        image_queries = result["image_queries"]

        lines = [
            "=" * 70,
            f"PRESENTATION PREVIEW",
            "=" * 70,
            f"\nTitle: {structure['title']}",
            f"Total Slides: {len(structure['slides']) + 1} (including title slide)",
            "\n" + "-" * 70,
        ]

        for i, slide in enumerate(structure.get("slides", []), 1):
            lines.append(f"\nSlide {i + 1}: {slide['title']}")
            
            if "image_theme" in slide and slide["image_theme"]:
                lines.append(f"  Image: {slide['image_theme']}")
            
            lines.append("  Points:")
            for point in slide.get("bullet_points", []):
                lines.append(f"    • {point}")

        if image_queries:
            lines.append("\n" + "-" * 70)
            lines.append("\nImage Queries:")
            for i, query in enumerate(image_queries, 1):
                lines.append(f"  {i}. {query}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)
