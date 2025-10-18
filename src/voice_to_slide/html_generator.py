"""HTML slide generation using Messages API."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from .utils import get_logger, ensure_directory

logger = get_logger(__name__)


class HTMLSlideGenerator:
    """Generates HTML slides using Messages API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        workspace_dir: str | Path = "workspace/slides"
    ):
        """Initialize the HTML generator.

        Args:
            api_key: Anthropic API key. If None, reads from CONTENT_ANTHROPIC_API_KEY.
            model: Claude model to use. If None, reads from CONTENT_MODEL.
            base_url: Custom API base URL. If None, reads from CONTENT_ANTHROPIC_BASE_URL.
            workspace_dir: Directory to save generated HTML files.
        """
        self.api_key = api_key or os.getenv("CONTENT_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set CONTENT_ANTHROPIC_API_KEY.")

        self.model = model or os.getenv("CONTENT_MODEL", "claude-haiku-4-5-20251001")
        self.base_url = base_url or os.getenv("CONTENT_ANTHROPIC_BASE_URL")
        self.workspace_dir = Path(workspace_dir)
        ensure_directory(self.workspace_dir)

        # Setup Anthropic client with prompt caching
        client_kwargs = {
            "api_key": self.api_key,
            "default_headers": {
                "anthropic-beta": "prompt-caching-2024-07-31"
            }
        }
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"Using custom base URL: {self.base_url}")
        
        self.client = Anthropic(**client_kwargs)
        logger.info("Prompt caching enabled")

        # Load themes
        self.themes_path = Path(__file__).parent / "themes.md"
        self.themes_content = self._load_themes()

        logger.info(f"HTMLSlideGenerator initialized with model: {self.model}")

    def _load_themes(self) -> str:
        """Load themes from themes.md file.

        Returns:
            Content of themes.md file
        """
        try:
            with open(self.themes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded themes from {self.themes_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to load themes: {e}")
            return ""

    def generate_slides_html(
        self,
        structure: Dict[str, Any],
        image_data: List[Optional[Dict[str, Any]]],
        theme: str = "Modern Professional",
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """Generate HTML files for all slides using Messages API.

        Args:
            structure: Presentation structure with title and slides
            image_data: List of image metadata dicts {url, width, height, description} (or None)
            theme: Theme name (from themes.md)
            output_dir: Output directory for HTML files (overrides workspace_dir)

        Returns:
            List of paths to generated HTML files
        """
        output_dir = output_dir or self.workspace_dir
        ensure_directory(output_dir)

        logger.info(f"Generating HTML slides with theme: {theme}")
        logger.info(f"Structure: {structure.get('title', 'Untitled')} with {len(structure.get('slides', []))} slides")

        html_files = []

        # Generate title slide (slide_00.html)
        logger.info("Generating title slide...")
        title_slide_path = self._generate_title_slide(
            title=structure.get("title", "Presentation"),
            theme=theme,
            output_dir=output_dir
        )
        html_files.append(title_slide_path)

        # Generate content slides
        slides = structure.get("slides", [])
        for i, slide_data in enumerate(slides, 1):
            logger.info(f"Generating slide {i}/{len(slides)}: {slide_data.get('title', '')}...")
            
            image_info = image_data[i-1] if i-1 < len(image_data) else None
            
            slide_path = self._generate_content_slide(
                slide_index=i,
                slide_data=slide_data,
                image_info=image_info,
                theme=theme,
                output_dir=output_dir
            )
            html_files.append(slide_path)

        logger.info(f"Generated {len(html_files)} HTML files")
        return html_files

    def _generate_title_slide(
        self,
        title: str,
        theme: str,
        output_dir: Path
    ) -> Path:
        """Generate HTML for title slide."""
        # Use structured content with cache_control for theme definitions
        prompt_content = [
            {
                "type": "text",
                "text": f"""Generate a complete HTML5 document for a presentation title slide.

**Theme**: {theme}

**Theme Definitions**:
{self._get_theme_excerpt(theme)}""",
                "cache_control": {"type": "ephemeral"}  # Cache theme definitions
            },
            {
                "type": "text",
                "text": f"""
**Content**:
- Title: {title}

**CRITICAL Requirements**:
1. Complete HTML5 document with DOCTYPE
2. Inline CSS styling (no external stylesheets)
3. **MUST fill entire viewport**: Use width: 100vw; height: 100vh for .slide container
4. **MUST add**: html, body {{ margin: 0; padding: 0; width: 100%; height: 100vh; overflow: hidden; }}
5. Use {theme} theme colors and typography
6. Centered layout with large, prominent title
7. Professional and clean design

**Output**: Return ONLY the complete HTML code, no explanations.
"""
            }
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt_content}]
        )

        html_content = response.content[0].text
        
        # Save to file
        output_path = output_dir / "slide_00.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ Generated: slide_00.html ({output_path.stat().st_size} bytes)")
        return output_path

    def _generate_content_slide(
        self,
        slide_index: int,
        slide_data: Dict[str, Any],
        image_info: Optional[Dict[str, Any]],
        theme: str,
        output_dir: Path
    ) -> Path:
        """Generate HTML for a content slide."""
        slide_title = slide_data.get("title", f"Slide {slide_index}")
        bullets = slide_data.get("bullet_points", [])
        bullets_text = "\n".join([f"  - {b}" for b in bullets])

        layout_instruction = ""
        if image_info and image_info.get("url"):
            image_url = image_info["url"]
            image_alt = image_info.get("description", "Slide image")
            layout_instruction = f"""**Layout**: Two-column (text left, image right)
- Left column (50% width): Title and bullet points
- Right column (50% width): Image

**IMAGE REQUIREMENTS - CRITICAL**:
- MUST include this exact HTML:
  <img src="{image_url}" alt="{image_alt}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">
- Image URL: {image_url}
- Image will be loaded by browser when rendering
- Image container must be 50% width of slide
- Image should be vertically centered
"""
        else:
            layout_instruction = "**Layout**: Full-width text (no image)"

        # Use structured content with cache_control for theme definitions
        prompt_content = [
            {
                "type": "text",
                "text": f"""Generate a complete HTML5 document for a presentation content slide.

**Theme**: {theme}

**Theme Definitions**:
{self._get_theme_excerpt(theme)}""",
                "cache_control": {"type": "ephemeral"}  # Cache theme definitions
            },
            {
                "type": "text",
                "text": f"""
**Content**:
- Title: {slide_title}
- Bullet points:
{bullets_text}

{layout_instruction}

**CRITICAL Requirements**:
1. Complete HTML5 document with DOCTYPE
2. Inline CSS styling (no external stylesheets)
3. **MUST fill entire viewport**: Use width: 100vw; height: 100vh for .slide container
4. **MUST add**: html, body {{ margin: 0; padding: 0; width: 100%; height: 100vh; overflow: hidden; }}
5. Use {theme} theme colors and typography
6. Professional typography and spacing
7. Bullet points should be clearly visible and well-spaced

**Output**: Return ONLY the complete HTML code, no explanations.
"""
            }
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt_content}]
        )

        html_content = response.content[0].text
        
        # Clean up any markdown artifacts
        if html_content.startswith("```html"):
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        elif html_content.startswith("```"):
            html_content = html_content.split("```")[1].split("```")[0].strip()
        
        # Save to file
        output_path = output_dir / f"slide_{slide_index:02d}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ Generated: slide_{slide_index:02d}.html ({output_path.stat().st_size} bytes)")
        return output_path

    def _get_theme_excerpt(self, theme: str) -> str:
        """Extract relevant theme section from themes.md."""
        lines = self.themes_content.split('\n')
        
        # Find the theme section
        start_idx = None
        for i, line in enumerate(lines):
            if f"## {theme}" in line or f"# {theme}" in line:
                start_idx = i
                break
        
        if start_idx is None:
            return self.themes_content  # Return full content if theme not found
        
        # Extract until next theme or end of file
        excerpt_lines = []
        for i in range(start_idx, len(lines)):
            line = lines[i]
            # Stop at next theme (but not at the current theme)
            if i > start_idx and (line.startswith("## ") or line.startswith("# Theme")):
                break
            excerpt_lines.append(line)
        
        return "\n".join(excerpt_lines)
