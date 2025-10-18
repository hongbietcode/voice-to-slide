"""Content summarization module using Tool Use (JSON mode)."""

import os
from typing import Dict, Any
from anthropic import Anthropic
from .utils import get_logger

logger = get_logger(__name__)


class ContentSummarizer:
    """Summarizes and breaks down transcription content using Tool Use."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        """Initialize the content summarizer.

        Args:
            api_key: Anthropic API key. If None, reads from SUMMARY_ANTHROPIC_API_KEY env var.
            base_url: API base URL. If None, reads from SUMMARY_ANTHROPIC_BASE_URL env var.
            model: Model to use. If None, reads from SUMMARY_MODEL env var.
        """
        self.api_key = api_key or os.getenv("SUMMARY_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Summary API key is required. Set SUMMARY_ANTHROPIC_API_KEY environment variable.")

        self.base_url = base_url or os.getenv("SUMMARY_ANTHROPIC_BASE_URL")
        self.model = model or os.getenv("SUMMARY_MODEL", "claude-3-5-sonnet-20241022")

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"Using custom base URL for summary: {self.base_url}")

        self.client = Anthropic(**client_kwargs)
        logger.info(f"ContentSummarizer initialized with model: {self.model}")

    def breakdown_and_summarize(self, transcription_text: str) -> Dict[str, Any]:
        """Break down and summarize transcription using Tool Use (JSON mode).

        Args:
            transcription_text: The full transcription text

        Returns:
            Dictionary containing structured breakdown
        """
        logger.info("Breaking down and summarizing transcription using Tool Use (JSON mode)")

        # Define the JSON schema as a tool - this GUARANTEES valid JSON output
        breakdown_tool = {
            "name": "record_breakdown",
            "description": "Record the comprehensive content breakdown and analysis",
            "input_schema": {
                "type": "object",
                "properties": {
                    "executive_summary": {
                        "type": "string",
                        "description": "2-3 sentence summary of core message and main takeaway"
                    },
                    "key_points": {
                        "type": "array",
                        "description": "5-8 most important points to highlight",
                        "items": {"type": "string"}
                    },
                    "main_topics": {
                        "type": "array",
                        "description": "3-5 primary themes or subjects",
                        "items": {"type": "string"}
                    },
                    "sections": {
                        "type": "array",
                        "description": "Detailed breakdown into logical sections",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "key_info": {"type": "string"},
                                "important_quotes": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "slide_suggestions": {"type": "string"}
                            },
                            "required": ["title", "key_info"]
                        }
                    },
                    "audience": {
                        "type": "string",
                        "description": "Target audience"
                    },
                    "tone": {
                        "type": "string",
                        "description": "Recommended presentation tone"
                    },
                    "recommended_structure": {
                        "type": "object",
                        "properties": {
                            "intro_slides": {"type": "integer"},
                            "content_slides": {"type": "integer"},
                            "conclusion_slides": {"type": "integer"},
                            "total_slides": {"type": "integer"}
                        },
                        "required": ["total_slides"]
                    }
                },
                "required": ["executive_summary", "key_points", "main_topics", "sections", "audience", "tone", "recommended_structure"]
            }
        }

        prompt = f"""Analyze and break down the following transcription into a structured summary suitable for creating a presentation.

Provide a comprehensive breakdown with:
1. Executive Summary (2-3 sentences)
2. Key Points (5-8 bullet points)
3. Main Topics (3-5 topics)
4. Detailed Breakdown by sections with titles, key info, quotes, and slide suggestions
5. Target Audience and recommended Tone
6. Recommended Structure for slides

TRANSCRIPTION:
{transcription_text}"""

        try:
            # Use tool use to FORCE valid JSON output according to schema
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=[breakdown_tool],
                tool_choice={"type": "tool", "name": "record_breakdown"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                                "cache_control": {"type": "ephemeral"}
                            }
                        ]
                    }
                ]
            )

            # Extract the structured data from tool_use block
            breakdown = None
            for block in response.content:
                if block.type == 'tool_use' and block.name == 'record_breakdown':
                    breakdown = block.input  # This is guaranteed valid JSON!
                    logger.info("✅ Successfully extracted structured breakdown from tool use")
                    break

            if not breakdown:
                raise ValueError("No tool_use block found in response")

            # Log cache performance
            usage = response.usage
            logger.info("Content breakdown completed successfully")
            logger.info(f"Cache performance: "
                       f"read={getattr(usage, 'cache_read_input_tokens', 0)}, "
                       f"created={getattr(usage, 'cache_creation_input_tokens', 0)}, "
                       f"input={getattr(usage, 'input_tokens', 0)}")

            return breakdown

        except Exception as e:
            logger.error(f"Failed to break down content: {e}")
            raise

    def create_enhanced_prompt(
        self,
        transcription_text: str,
        breakdown: Dict[str, Any]
    ) -> str:
        """Create an enhanced prompt for presentation generation using the breakdown.

        Args:
            transcription_text: Original transcription
            breakdown: The breakdown analysis

        Returns:
            Enhanced prompt string
        """
        sections_text = ""
        for i, section in enumerate(breakdown.get('sections', []), 1):
            sections_text += f"\n{i}. {section.get('title', 'Section')}\n"
            sections_text += f"   - {section.get('key_info', '')}\n"
            if section.get('important_quotes'):
                sections_text += f"   - Quotes: {', '.join(section['important_quotes'][:2])}\n"

        structure = breakdown.get('recommended_structure', {})

        enhanced_prompt = f"""Create a professional presentation based on this analyzed content.

EXECUTIVE SUMMARY:
{breakdown.get('executive_summary', '')}

KEY POINTS TO HIGHLIGHT:
{chr(10).join(f"• {point}" for point in breakdown.get('key_points', []))}

MAIN TOPICS:
{', '.join(breakdown.get('main_topics', []))}

CONTENT BREAKDOWN:
{sections_text}

TARGET AUDIENCE: {breakdown.get('audience', 'General audience')}
TONE: {breakdown.get('tone', 'Professional')}

RECOMMENDED STRUCTURE:
- Intro slides: {structure.get('intro_slides', 1)}
- Content slides: {structure.get('content_slides', 6)}
- Conclusion slides: {structure.get('conclusion_slides', 1)}
- Total: {structure.get('total_slides', 8)} slides

ORIGINAL TRANSCRIPTION (for reference):
{transcription_text[:1000]}...

Please create a presentation that:
1. Follows the recommended structure above
2. Emphasizes the key points identified
3. Uses the main topics as organizing themes
4. Matches the target audience and tone
5. Creates visually appealing slides with clear hierarchy
"""

        return enhanced_prompt
