"""Helper to analyze transcription using Tool Use (JSON mode)."""

import json
from typing import Dict, Any
from anthropic import Anthropic
from .utils import get_logger

logger = get_logger(__name__)


def analyze_transcription_with_tool_use(
    client: Anthropic,
    model: str,
    transcription_text: str
) -> Dict[str, Any]:
    """Analyze transcription using Tool Use to guarantee valid JSON.
    
    Args:
        client: Anthropic client instance
        model: Model to use
        transcription_text: The transcribed text
        
    Returns:
        Dictionary with suggested structure
    """
    logger.info("Analyzing transcription using Tool Use (JSON mode)")
    
    # Define JSON schema as a tool
    analysis_tool = {
        "name": "record_analysis",
        "description": "Record the presentation structure analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Compelling presentation title"
                },
                "num_slides": {
                    "type": "integer",
                    "description": "Suggested number of slides (5-10)"
                },
                "sections": {
                    "type": "array",
                    "description": "Main sections/topics to cover",
                    "items": {"type": "string"}
                },
                "key_messages": {
                    "type": "array",
                    "description": "Key messages to emphasize",
                    "items": {"type": "string"}
                },
                "image_themes": {
                    "type": "array",
                    "description": "Suggested visual themes/images for sections",
                    "items": {"type": "string"}
                }
            },
            "required": ["title", "num_slides", "sections", "key_messages", "image_themes"]
        }
    }
    
    prompt = f"""Analyze the following transcription and suggest a presentation structure.

Provide:
1. A compelling presentation title
2. Suggested number of slides (5-10)
3. Main sections/topics to cover
4. Key messages to emphasize
5. Suggested visual themes/images for each section

TRANSCRIPTION:
{transcription_text}"""
    
    try:
        # Use tool use to force valid JSON
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            tools=[analysis_tool],
            tool_choice={"type": "tool", "name": "record_analysis"},
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
        
        # Extract structured data
        structure = None
        for block in response.content:
            if block.type == 'tool_use' and block.name == 'record_analysis':
                structure = block.input
                logger.info("✅ Successfully extracted analysis from tool use")
                break
        
        if not structure:
            raise ValueError("No tool_use block found in response")
        
        # Log cache performance
        usage = response.usage
        logger.info(f"Analysis complete: {structure.get('num_slides', 0)} slides suggested")
        logger.info(f"Cache performance: "
                   f"read={getattr(usage, 'cache_read_input_tokens', 0)}, "
                   f"created={getattr(usage, 'cache_creation_input_tokens', 0)}, "
                   f"input={getattr(usage, 'input_tokens', 0)}")
        
        return structure
        
    except Exception as e:
        logger.error(f"Failed to analyze transcription: {e}")
        raise
