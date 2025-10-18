"""Convert HTML to images using Playwright."""

import os
from pathlib import Path
from typing import List, Optional
from playwright.sync_api import sync_playwright, Browser, Page
from .utils import get_logger, ensure_directory

logger = get_logger(__name__)


class HTMLToImageConverter:
    """Converts HTML files to PNG images using Playwright."""

    def __init__(self, headless: bool = True):
        """Initialize converter.

        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless
        logger.info(f"HTMLToImageConverter initialized (headless={headless})")

    def convert_html_to_image(
        self,
        html_path: Path,
        output_path: Path,
        width: int = 960,
        height: int = 540
    ) -> Path:
        """Convert a single HTML file to PNG image.

        Args:
            html_path: Path to HTML file
            output_path: Path to save PNG image
            width: Viewport width in pixels (default: 960)
            height: Viewport height in pixels (default: 540)

        Returns:
            Path to generated PNG image
        """
        logger.info(f"Converting {html_path.name} to PNG...")

        ensure_directory(output_path.parent)

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)
            
            # Create context with specific viewport size
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2  # Retina display for better quality
            )
            
            # Create page
            page = context.new_page()
            
            try:
                # Load HTML file (use file:// protocol)
                html_url = f"file://{html_path.absolute()}"
                logger.debug(f"Loading: {html_url}")
                page.goto(html_url, wait_until="networkidle")
                
                # Wait for any fonts/resources to load
                page.wait_for_timeout(1000)  # 1 second
                
                # Take screenshot
                page.screenshot(
                    path=str(output_path),
                    full_page=False,  # Exact viewport size
                    type="png"
                )
                
                logger.info(f"✓ Generated: {output_path.name} ({output_path.stat().st_size} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to convert {html_path}: {e}")
                raise
                
            finally:
                browser.close()

        return output_path

    def convert_html_files_to_images(
        self,
        html_files: List[Path],
        output_dir: Path,
        width: int = 960,
        height: int = 540
    ) -> List[Path]:
        """Convert multiple HTML files to PNG images.

        Args:
            html_files: List of HTML file paths
            output_dir: Output directory for images
            width: Viewport width
            height: Viewport height

        Returns:
            List of paths to generated PNG images
        """
        logger.info(f"Converting {len(html_files)} HTML files to images...")

        ensure_directory(output_dir)
        image_paths = []

        with sync_playwright() as p:
            # Launch browser once for all conversions
            browser = p.chromium.launch(headless=self.headless)
            
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2
            )
            
            page = context.new_page()

            try:
                for html_file in html_files:
                    # Generate output path
                    output_path = output_dir / f"{html_file.stem}.png"
                    
                    # Load and screenshot
                    html_url = f"file://{html_file.absolute()}"
                    page.goto(html_url, wait_until="networkidle")
                    page.wait_for_timeout(500)  # Wait for fonts
                    
                    page.screenshot(
                        path=str(output_path),
                        full_page=False,
                        type="png"
                    )
                    
                    image_paths.append(output_path)
                    logger.info(f"✓ Generated: {output_path.name}")

            except Exception as e:
                logger.error(f"Batch conversion failed: {e}")
                raise
                
            finally:
                browser.close()

        logger.info(f"Generated {len(image_paths)} images")
        return image_paths


def convert_html_to_image(
    html_path: Path,
    output_path: Path,
    width: int = 960,
    height: int = 540,
    headless: bool = True
) -> Path:
    """Convenience function to convert single HTML to image.

    Args:
        html_path: HTML file path
        output_path: Output image path
        width: Viewport width
        height: Viewport height
        headless: Run headless

    Returns:
        Path to generated image
    """
    converter = HTMLToImageConverter(headless=headless)
    return converter.convert_html_to_image(html_path, output_path, width, height)


def convert_html_files_to_images(
    html_files: List[Path],
    output_dir: Path,
    width: int = 960,
    height: int = 540,
    headless: bool = True
) -> List[Path]:
    """Convenience function to convert multiple HTML files to images.

    Args:
        html_files: List of HTML file paths
        output_dir: Output directory
        width: Viewport width
        height: Viewport height
        headless: Run headless

    Returns:
        List of generated image paths
    """
    converter = HTMLToImageConverter(headless=headless)
    return converter.convert_html_files_to_images(html_files, output_dir, width, height)
