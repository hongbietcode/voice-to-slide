"""Presentation generation module using Claude Agent SDK with PPTX skill."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from anthropic import Anthropic
from .utils import get_logger, ensure_directory
from .presentation_analyzer import analyze_transcription_with_tool_use

logger = get_logger(__name__)

class PresentationGenerator:
    """Generates PowerPoint presentations using Claude with PPTX skill."""

    def __init__(self, api_key: str | None = None, model: str = "claude-haiku-4-5-20251001"):
        """Initialize the presentation generator.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("PRESENTATION_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set PRESENTATION_ANTHROPIC_API_KEY environment variable.")

        # Support custom base URL for API endpoint
        base_url = os.getenv("PRESENTATION_ANTHROPIC_BASE_URL")
        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            logger.info(f"Using custom Anthropic base URL: {base_url}")

        self.client = Anthropic(**client_kwargs)
        self.model = os.getenv("PRESENTATION_MODEL", model)

        # Load custom skill ID if available
        self.custom_skill_id = self._load_custom_skill_id()

        logger.info(f"PresentationGenerator initialized with model: {self.model}")
        if self.custom_skill_id:
            logger.info(f"Using custom PPTX skill: {self.custom_skill_id}")
        else:
            logger.info("Using Anthropic PPTX skill (default)")

    def _load_custom_skill_id(self) -> Optional[str]:
        """Load custom skill ID from environment variable.

        Returns:
            Custom skill ID if available, None otherwise (will use Anthropic default)
        """
        skill_id = os.getenv("CUSTOM_PPTX_SKILL_ID")
        if skill_id:
            logger.info(f"Using custom PPTX skill from env: {skill_id}")
        return skill_id

    def _get_cached_images(self) -> Dict[int, str]:
        """Get cached image files from .cache/images/ directory.

        Returns:
            Dictionary mapping slide index to actual filename
        """
        cache_dir = Path(".cache/images")
        if not cache_dir.exists():
            logger.warning("Cache directory .cache/images/ does not exist")
            return {}

        cached_images = {}
        try:
            # List all files in cache directory
            files = list(cache_dir.glob("slide_*.jpg"))
            logger.info(f"Found {len(files)} cached images in {cache_dir}")

            for file in files:
                # Extract slide index from filename (slide_00_*.jpg -> 0)
                filename = file.name
                if filename.startswith("slide_") and filename.endswith(".jpg"):
                    try:
                        # Extract index from slide_00_*.jpg
                        index_str = filename.split("_")[1]
                        index = int(index_str)
                        # Store relative path from project root
                        cached_images[index] = str(file)
                        logger.debug(f"Slide {index}: {file.name}")
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Could not parse index from {filename}: {e}")

            return cached_images

        except Exception as e:
            logger.error(f"Error reading cached images: {e}")
            return {}

    def generate_presentation(
        self,
        transcription_text: str,
        image_queries: Optional[list[str]] = None,
        output_path: Path | str = "presentation.pptx",
        enhance: bool = True
    ) -> Dict[str, Any]:
        """Generate a complete PowerPoint presentation from transcribed text.

        Args:
            transcription_text: The transcribed audio text
            image_queries: Optional list of image search queries for slides
            output_path: Path where the PPTX file should be saved
            enhance: Whether to enhance content quality (takes longer)

        Returns:
            Dictionary with generation results including file_id and status
        """
        logger.info("Generating presentation using Claude with PPTX skill")

        # Construct the prompt for Claude
        prompt_parts = self._build_presentation_prompt(
            transcription_text,
            image_queries,
            enhance
        )

        # Log the full prompt for transparency
        logger.info("=" * 80)
        logger.info("PROMPT TO BE SENT TO CLAUDE:")
        logger.info("=" * 80)
        logger.info(prompt_parts["instruction"] + prompt_parts["content"][:200] + "...")
        # Determine which skill to use
        if self.custom_skill_id:
            skill_config = {
                "type": "custom",
                "skill_id": self.custom_skill_id,
                "version": "latest"
            }
            skill_name = f"pptx-enhanced (custom: {self.custom_skill_id})"
        else:
            skill_config = {
                "type": "anthropic",
                "skill_id": "pptx",
                "version": "latest"
            }
            skill_name = "pptx (Anthropic)"

        logger.info("=" * 80)
        logger.info(f"Model: {self.model}")
        logger.info(f"Max tokens: 8192")
        logger.info(f"Skill: {skill_name}")
        logger.info(f"Caching: enabled for transcription content")
        logger.info("=" * 80)

        try:
            # Create message with PPTX skill (custom or Anthropic)
            # The prompt will guide Claude to use cached images and generate charts
            # Use prompt caching for the large transcription content
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=8192,
                betas=["code-execution-2025-08-25", "skills-2025-10-02"],
                container={
                    "skills": [skill_config]
                },
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_parts["instruction"]
                            },
                            {
                                "type": "text",
                                "text": prompt_parts["content"],
                                "cache_control": {"type": "ephemeral"}
                            }
                        ]
                    }
                ],
                tools=[
                    {
                        "type": "code_execution_20250825",
                        "name": "code_execution"
                    }
                ]
            )

            # Extract file_id from response (as per official docs)
            # https://docs.claude.com/en/docs/agents-and-tools/tool-use/code-execution-tool#retrieve-generated-files

            # Debug: Log full response for troubleshooting
            logger.info("=" * 80)
            logger.info("CLAUDE RESPONSE DEBUG:")
            logger.info("=" * 80)
            logger.info(f"Response has {len(response.content)} content blocks")

            # Log all content blocks with details
            for i, item in enumerate(response.content):
                item_type = getattr(item, 'type', 'unknown')
                logger.info(f"\nBlock {i}:")
                logger.info(f"  Type: {item_type}")

                # If it's a text block, show the text
                if item_type == 'text':
                    text_content = getattr(item, 'text', '')
                    logger.info(f"  Text: {text_content[:500]}...")

                # If it's a tool use, show the tool details
                elif item_type == 'tool_use':
                    tool_name = getattr(item, 'name', 'unknown')
                    logger.info(f"  Tool: {tool_name}")
                    logger.info(f"  Input: {str(getattr(item, 'input', {}))[:200]}...")

                # Show all attributes for debugging
                logger.debug(f"  All attributes: {dir(item)}")

            logger.info("=" * 80)

            # Check stop reason
            stop_reason = getattr(response, 'stop_reason', None)
            logger.info(f"Stop reason: {stop_reason}")

            # Check usage
            usage = getattr(response, 'usage', None)
            if usage:
                logger.info(f"Token usage: input={usage.input_tokens}, output={usage.output_tokens}")

            file_ids = []
            for item in response.content:
                item_type = getattr(item, 'type', None)
                logger.debug(f"Checking item type: {item_type}")
                
                # Look for bash_code_execution_tool_result or text_editor_code_execution_tool_result
                if item_type in ['bash_code_execution_tool_result', 'text_editor_code_execution_tool_result']:
                    content_item = item.content
                    content_type = getattr(content_item, 'type', None)
                    logger.info(f"Found tool result, content type: {content_type}")
                    
                    # Check if it's a bash result with files
                    if content_type == 'bash_code_execution_result':
                        # Iterate through content to find files
                        if hasattr(content_item, 'content') and isinstance(content_item.content, list):
                            logger.info(f"Content has {len(content_item.content)} items")
                            for file_item in content_item.content:
                                if hasattr(file_item, 'file_id'):
                                    file_ids.append(file_item.file_id)
                                    logger.info(f"✅ Found file_id: {file_item.file_id}")
                                else:
                                    logger.debug(f"Item type: {type(file_item)}, has file_id: {hasattr(file_item, 'file_id')}")
            
            # Use the first file_id if any were found
            file_id = file_ids[0] if file_ids else None
            
            if not file_id:
                logger.warning("No file_id found in response. This might be expected if Claude hasn't finished generating the file yet.")

                # Save full response to debug file
                debug_path = Path(output_path).with_suffix('.debug.json')
                try:
                    debug_data = {
                        "stop_reason": stop_reason,
                        "model": self.model,
                        "content_blocks": [
                            {
                                "type": getattr(item, 'type', 'unknown'),
                                "text": getattr(item, 'text', None) if hasattr(item, 'text') else None,
                                "name": getattr(item, 'name', None) if hasattr(item, 'name') else None,
                            }
                            for item in response.content
                        ]
                    }
                    with open(debug_path, 'w') as f:
                        json.dump(debug_data, f, indent=2)
                    logger.info(f"Debug info saved to: {debug_path}")
                except Exception as e:
                    logger.error(f"Failed to save debug info: {e}")

            result = {
                "status": "success" if file_id else "partial",
                "file_id": file_id,
                "response": response,
                "output_path": str(output_path)
            }

            # Log cache performance
            usage = response.usage
            logger.info(f"Cache performance: "
                       f"read={getattr(usage, 'cache_read_input_tokens', 0)}, "
                       f"created={getattr(usage, 'cache_creation_input_tokens', 0)}, "
                       f"input={getattr(usage, 'input_tokens', 0)}")

            # Download the file if we got a file_id
            if file_id:
                self._download_presentation(file_id, output_path)
                logger.info(f"Presentation generated successfully: {output_path}")
            else:
                logger.warning("Presentation generated but no file_id found in response")

            return result

        except Exception as e:
            logger.error(f"Failed to generate presentation: {e}")
            raise

    def _build_presentation_prompt(
        self,
        transcription_text: str,
        image_queries: Optional[list[str]],
        enhance: bool
    ) -> dict:
        """Build the prompt for Claude to generate the presentation.

        Args:
            transcription_text: The transcribed text
            image_queries: Optional image search queries
            enhance: Whether to enhance content

        Returns:
            Dictionary with instruction and content for caching
        """
        # Get actual cached image files
        cached_images = self._get_cached_images() if image_queries else {}
        instruction = """Create a professional PowerPoint presentation from the following transcribed audio content.

STEP 1 - CHECK FOR CACHED IMAGES (CRITICAL):
First, check if images are available in .cache/images/ directory:
```javascript
const fs = require('fs');
const cacheDir = '.cache/images';
if (fs.existsSync(cacheDir)) {
    console.log('Available cached images:');
    console.log(fs.readdirSync(cacheDir));
}
```

STEP 2 - HELPER FUNCTION TO LOAD IMAGES:
Use this helper function in your presentation code:
```javascript
function getCachedImage(slideIndex) {
    const cacheDir = '.cache/images';
    if (!fs.existsSync(cacheDir)) return null;
    const files = fs.readdirSync(cacheDir);
    const prefix = `slide_${String(slideIndex).padStart(2, '0')}_`;
    const imageFile = files.find(f => f.startsWith(prefix) && f.endsWith('.jpg'));
    return imageFile ? path.join(cacheDir, imageFile) : null;
}
```

STEP 3 - PRESENTATION REQUIREMENTS:
1. Create 5-10 slides that logically organize the content
2. For EACH slide, check if there's a cached image using getCachedImage(slideIndex)
3. If image exists, use it as:
   - Full-bleed background (with dark overlay for text readability)
   - OR in content area (two-column layout: 40% text, 60% image)

DESIGN GUIDELINES:
- Slide format: 16:9 widescreen (10" × 5.625")
- Professional color scheme with strong contrast
- Web-safe fonts: Arial, Helvetica, Calibri
- Proper text spacing to avoid cutoff
- Centered text alignment for titles
- Left-aligned bullet points with adequate margins (min 0.5" from edges)

LAYOUT PATTERNS:
Pattern A - Title Slide with Background Image:
```javascript
const img = getCachedImage(0);
if (img && fs.existsSync(img)) {
    slide.addImage({ path: img, x: 0, y: 0, w: 10, h: 5.625 });
    // Add dark overlay for text readability
    slide.addShape(pptx.ShapeType.rect, {
        x: 0, y: 1.5, w: 10, h: 2.5,
        fill: { color: "000000", transparency: 50 }
    });
    slide.addText("Your Title", {
        x: 1, y: 2, w: 8, h: 1,
        fontSize: 44, bold: true, color: "FFFFFF", align: "center"
    });
}
```

Pattern B - Content Slide with Side Image:
```javascript
const img = getCachedImage(1);
// Text column (left 40%)
slide.addText("Key Points", { x: 0.5, y: 0.5, w: 4, h: 0.6, fontSize: 32, bold: true });
slide.addText([
    { text: "Point 1", options: { bullet: true } },
    { text: "Point 2", options: { bullet: true } },
    { text: "Point 3", options: { bullet: true } }
], { x: 0.5, y: 1.5, w: 4, h: 3.5, fontSize: 18 });

// Image (right 60%)
if (img && fs.existsSync(img)) {
    slide.addImage({ path: img, x: 5, y: 0.5, w: 4.5, h: 4.5 });
}
```

DATA VISUALIZATION (if applicable):
- Generate charts using matplotlib (300 DPI PNG)
- Save to workspace/ directory
- Use same two-column layout pattern

CRITICAL RULES:
1. ALWAYS check .cache/images/ directory at the start
2. ALWAYS use getCachedImage() helper for each slide
3. NEVER skip images if they exist in cache
4. ENSURE text has proper margins (min 0.5" from all edges)
5. USE overlays on background images for text readability
6. TEST layout by generating thumbnails

{'ENHANCED MODE: Make content engaging and use ALL available cached images creatively.' if enhance else ''}

CRITICAL - FINAL STEP:
After creating the presentation code, you MUST:
1. Execute the code using the code execution tool
2. Generate the PPTX file
3. Return the file so it can be downloaded

DO NOT just explain the code. DO NOT ask for confirmation. EXECUTE IT NOW and create the PPTX file."""

        if image_queries and cached_images:
            instruction += f"\n\n{'=' * 60}\n"
            instruction += f"CACHED IMAGES AVAILABLE:\n"
            instruction += f"{'=' * 60}\n"
            for i, query in enumerate(image_queries):
                image_file = cached_images.get(i)
                if image_file:
                    instruction += f"Slide {i}: {query}\n"
                    instruction += f"  → File: {image_file}\n"
                    instruction += f"  → Load with: slide.addImage({{ path: '{image_file}', ... }})\n"
                else:
                    instruction += f"Slide {i}: {query}\n"
                    instruction += f"  → No cached image found (skip or use placeholder)\n"
            instruction += f"\n{'=' * 60}\n"
            instruction += f"YOU MUST:\n"
            instruction += f"1. Use the EXACT file paths listed above\n"
            instruction += f"2. Add images to presentation (background or content area)\n"
            instruction += f"3. Verify all images are included in final PPTX\n"
            instruction += f"4. Check files exist with fs.existsSync() before adding\n"
            instruction += f"{'=' * 60}\n"

        return {
            "instruction": instruction,
            "content": f"\n\nTRANSCRIPTION:\n{transcription_text}"
        }

    def _download_presentation(self, file_id: str, output_path: Path | str) -> None:
        """Download the generated presentation file.

        Args:
            file_id: File ID from Claude's response
            output_path: Where to save the file
        """
        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        try:
            # Download file using beta Files API
            file_content = self.client.beta.files.download(
                file_id=file_id,
                betas=["files-api-2025-04-14"]
            )

            # Save to disk using the documented method
            file_content.write_to_file(str(output_path))

            logger.info(f"Downloaded presentation to {output_path}")

        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            raise

    def preview_prompt(
        self,
        transcription_text: str,
        image_queries: Optional[list[str]] = None,
        enhance: bool = True
    ) -> str:
        """Preview the prompt that will be sent to Claude without generating.

        Args:
            transcription_text: The transcribed audio text
            image_queries: Optional list of image search queries for slides
            enhance: Whether to enhance content quality

        Returns:
            The formatted prompt string
        """
        prompt_parts = self._build_presentation_prompt(
            transcription_text,
            image_queries,
            enhance
        )
        return prompt_parts["instruction"] + prompt_parts["content"]

    def analyze_transcription(self, transcription_text: str) -> Dict[str, Any]:
        """Analyze transcription and suggest presentation structure using Tool Use.

        Args:
            transcription_text: The transcribed text

        Returns:
            Dictionary with suggested structure
        """
        # Use the helper function that implements Tool Use (JSON mode)
        return analyze_transcription_with_tool_use(
            self.client,
            self.model,
            transcription_text
        )

