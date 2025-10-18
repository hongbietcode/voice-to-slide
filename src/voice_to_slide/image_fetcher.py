"""Image fetching module using Unsplash API."""

import os
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
from .utils import get_logger, ensure_directory

logger = get_logger(__name__)

class ImageFetcher:
    """Fetches relevant images from Unsplash API."""

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | str = ".cache/images",
        max_width: int = 1920,
        max_height: int = 1080
    ):
        """Initialize the image fetcher.

        Args:
            api_key: Unsplash Access Key. If None, reads from UNSPLASH_ACCESS_KEY env var.
            cache_dir: Directory to cache downloaded images
            max_width: Maximum width for resized images (default: 1920px for Full HD)
            max_height: Maximum height for resized images (default: 1080px for Full HD)
        """
        self.api_key = api_key or os.getenv("UNSPLASH_ACCESS_KEY")
        if not self.api_key:
            raise ValueError("Unsplash API key is required. Set UNSPLASH_ACCESS_KEY environment variable.")

        self.base_url = "https://api.unsplash.com"
        self.cache_dir = Path(cache_dir)
        self.max_width = max_width
        self.max_height = max_height
        ensure_directory(self.cache_dir)

        logger.info(f"ImageFetcher initialized (max size: {max_width}x{max_height})")

    def search_photo(
        self,
        query: str,
        orientation: str = "landscape",
        per_page: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Search for a photo on Unsplash.

        Args:
            query: Search query (e.g., "business meeting", "data analytics")
            orientation: Photo orientation (landscape, portrait, squarish)
            per_page: Number of results to return

        Returns:
            Photo data dictionary or None if no results found
        """
        logger.info(f"Searching Unsplash for: {query}")

        url = f"{self.base_url}/search/photos"
        headers = {
            "Authorization": f"Client-ID {self.api_key}"
        }
        params = {
            "query": query,
            "orientation": orientation,
            "per_page": per_page
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(f"No images found for query: {query}")
                return None

            photo = results[0]
            logger.info(f"Found image by {photo['user']['name']}")

            return {
                "id": photo["id"],
                "url": photo["urls"]["regular"],
                "download_url": photo["urls"]["full"],
                "description": photo.get("description") or photo.get("alt_description", ""),
                "author": photo["user"]["name"],
                "author_url": photo["user"]["links"]["html"],
                "photo_url": photo["links"]["html"]
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search Unsplash: {e}")
            return None

    def download_photo(
        self,
        photo_data: Dict[str, Any],
        filename: Optional[str] = None,
        resize: bool = True
    ) -> Optional[Path]:
        """Download and optionally resize a photo from Unsplash.

        Args:
            photo_data: Photo data dictionary from search_photo()
            filename: Optional custom filename. If None, uses photo ID.
            resize: Whether to resize image to max dimensions (default: True)

        Returns:
            Path to downloaded image file or None if download failed
        """
        if not photo_data:
            return None

        if filename is None:
            filename = f"{photo_data['id']}.jpg"

        filepath = self.cache_dir / filename

        # Check if already cached
        if filepath.exists():
            logger.info(f"Using cached image: {filepath}")
            return filepath

        logger.info(f"Downloading image to: {filepath}")

        try:
            # Trigger download endpoint (required by Unsplash API guidelines)
            download_url = photo_data.get("download_url") or photo_data.get("url")
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            # Save temporarily
            temp_path = filepath.with_suffix('.tmp.jpg')
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            # Resize if enabled
            if resize:
                self._resize_image(temp_path, filepath)
                temp_path.unlink()  # Remove temp file
            else:
                temp_path.rename(filepath)

            logger.info(f"Image downloaded successfully: {filepath}")
            return filepath

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            # Clean up temp file if exists
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            return None

    def _resize_image(self, input_path: Path, output_path: Path) -> None:
        """Resize image to fit within max dimensions while preserving aspect ratio.

        Args:
            input_path: Path to input image
            output_path: Path to save resized image
        """
        try:
            with Image.open(input_path) as img:
                original_size = img.size
                logger.info(f"Original image size: {original_size[0]}x{original_size[1]}px")

                # Check if resize is needed
                if img.width <= self.max_width and img.height <= self.max_height:
                    logger.info("Image already within limits, no resize needed")
                    img.save(output_path, 'JPEG', quality=85, optimize=True)
                    return

                # Calculate new size maintaining aspect ratio
                img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                new_size = img.size

                logger.info(f"Resized image to: {new_size[0]}x{new_size[1]}px "
                           f"(reduced by {100 - (new_size[0] * new_size[1] * 100 / (original_size[0] * original_size[1])):.1f}%)")

                # Save with optimization
                img.save(output_path, 'JPEG', quality=85, optimize=True)

                # Log file size reduction
                input_size = input_path.stat().st_size / 1024 / 1024
                output_size = output_path.stat().st_size / 1024 / 1024
                logger.info(f"File size: {input_size:.2f}MB → {output_size:.2f}MB "
                           f"(saved {input_size - output_size:.2f}MB)")

        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            # Fall back to copying original
            with open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    f_out.write(f_in.read())

    def get_image_urls_for_presentation(self, queries: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Get image URLs and metadata without downloading.

        Args:
            queries: List of search queries for each slide

        Returns:
            List of dicts with {url, width, height, description} or None for failed queries
        """
        if not queries:
            return []

        logger.info(f"Fetching image URLs for {len(queries)} slides...")

        results = []
        for i, query in enumerate(queries):
            try:
                logger.debug(f"Searching Unsplash for: {query}")
                
                headers = {"Authorization": f"Client-ID {self.api_key}"}
                response = requests.get(
                    f"{self.base_url}/search/photos",
                    headers=headers,
                    params={
                        "query": query,
                        "per_page": 1,
                        "orientation": "landscape"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("results"):
                        photo = data["results"][0]
                        image_info = {
                            "url": photo["urls"]["regular"],  # High quality URL (~1080px width)
                            "width": photo["width"],
                            "height": photo["height"],
                            "description": photo.get("description") or photo.get("alt_description") or query,
                            "photographer": photo["user"]["name"],
                            "photographer_url": photo["user"]["links"]["html"]
                        }
                        results.append(image_info)
                        logger.info(f"✓ Found image for '{query}': {photo['urls']['regular'][:60]}...")
                    else:
                        logger.warning(f"No images found for '{query}'")
                        results.append(None)
                else:
                    logger.error(f"Unsplash API error: {response.status_code}")
                    results.append(None)
                    
            except Exception as e:
                logger.error(f"Failed to fetch image URL for '{query}': {e}")
                results.append(None)

        successful = sum(1 for r in results if r is not None)
        logger.info(f"Successfully fetched {successful}/{len(queries)} image URLs")
        
        return results

    def fetch_image_for_slide(
        self,
        query: str,
        slide_index: int = 0
    ) -> Optional[Path]:
        """Convenience method to search and download an image for a slide.

        Args:
            query: Search query
            slide_index: Slide number (for filename)

        Returns:
            Path to downloaded image or None
        """
        photo_data = self.search_photo(query)
        if not photo_data:
            return None

        filename = f"slide_{slide_index:02d}_{photo_data['id']}.jpg"
        return self.download_photo(photo_data, filename)

    def fetch_images_for_presentation(
        self,
        image_queries: list[str]
    ) -> list[Optional[Path]]:
        """Fetch images for all slides in a presentation.

        Args:
            image_queries: List of search queries, one per slide

        Returns:
            List of image paths (None for failed downloads)
        """
        logger.info(f"Fetching {len(image_queries)} images for presentation")

        image_paths = []
        for i, query in enumerate(image_queries):
            if not query:
                logger.warning(f"Slide {i}: Empty query, skipping image")
                image_paths.append(None)
                continue

            image_path = self.fetch_image_for_slide(query, i)
            image_paths.append(image_path)

        successful = sum(1 for p in image_paths if p is not None)
        logger.info(f"Successfully fetched {successful}/{len(image_queries)} images")

        return image_paths
