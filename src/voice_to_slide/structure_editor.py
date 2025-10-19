"""AI-powered structure editor using Claude Messages API."""

import os
from typing import Dict, Any
from anthropic import Anthropic
from .utils import get_logger

logger = get_logger(__name__)


class StructureEditor:
    """Edits presentation structure based on user feedback using Claude."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the structure editor.

        Args:
            api_key: Anthropic API key. If None, reads from CONTENT_ANTHROPIC_API_KEY.
            model: Claude model to use. If None, reads from CONTENT_MODEL.
        """
        self.api_key = api_key or os.getenv("CONTENT_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set CONTENT_ANTHROPIC_API_KEY.")

        self.model = model or os.getenv("CONTENT_MODEL", "claude-haiku-4-5-20251001")

        # Setup client with prompt caching enabled
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
        logger.info(f"StructureEditor initialized with model: {self.model}")
        logger.info("Prompt caching enabled for feedback loop")

    def edit_structure(
        self,
        current_structure: Dict[str, Any],
        user_feedback: str
    ) -> Dict[str, Any]:
        """Edit structure based on user feedback with prompt caching.

        Args:
            current_structure: Current presentation structure
            user_feedback: User's feedback/instructions for editing

        Returns:
            Updated structure
        """
        logger.info(f"Editing structure based on feedback: {user_feedback[:100]}...")

        # Structured content blocks for optimal caching
        # Block 1: Instructions (cached - static across all requests)
        # Block 2: Current structure (cached - reused until edited)
        # Block 3: User feedback (fresh - changes each request)

        prompt_content = [
            {
                "type": "text",
                "text": """You are a presentation structure editor. Edit the following presentation structure based on the user's feedback.

INSTRUCTIONS:
1. Analyze the user's feedback carefully
2. Make the requested changes to the structure
3. Maintain the same JSON format
4. Ensure all required fields are present (title, slides with title and bullet_points)
5. Return ONLY the updated JSON structure, no explanations

OUTPUT FORMAT:
```json
{
  "title": "Presentation Title",
  "slides": [
    {
      "title": "Slide Title",
      "bullet_points": ["Point 1", "Point 2", "Point 3"],
      "image_theme": "optional search query"
    }
  ]
}
```

Return the complete updated structure.""",
                "cache_control": {"type": "ephemeral"}  # Cache instructions
            },
            {
                "type": "text",
                "text": f"""CURRENT STRUCTURE:
```json
{self._format_structure(current_structure)}
```""",
                "cache_control": {"type": "ephemeral"}  # Cache structure
            },
            {
                "type": "text",
                "text": f"""USER FEEDBACK:
{user_feedback}

Please return the updated structure:"""
            }
        ]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt_content
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Clean up markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            import json
            updated_structure = json.loads(response_text)

            # Log cache usage for debugging
            usage = response.usage
            if hasattr(usage, 'cache_creation_input_tokens') or hasattr(usage, 'cache_read_input_tokens'):
                logger.info(f"Cache stats - Created: {getattr(usage, 'cache_creation_input_tokens', 0)} tokens, "
                           f"Read: {getattr(usage, 'cache_read_input_tokens', 0)} tokens, "
                           f"Regular: {getattr(usage, 'input_tokens', 0)} tokens")

            logger.info("Structure updated successfully")
            return updated_structure

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse updated structure: {e}")
            logger.error(f"Response was: {response_text[:200]}")
            raise ValueError(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to edit structure: {e}")
            raise

    def _format_structure(self, structure: Dict[str, Any]) -> str:
        """Format structure as JSON string.

        Args:
            structure: Structure dict

        Returns:
            Formatted JSON string
        """
        import json
        return json.dumps(structure, indent=2, ensure_ascii=False)
