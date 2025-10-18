"""Utility functions for the voice-to-slide application."""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with configurable log level.
    
    Set LOG_LEVEL environment variable to control verbosity:
    - DEBUG: Detailed information for debugging
    - INFO: General information (default)
    - WARNING: Warning messages only
    - ERROR: Error messages only
    """
    import os
    logger = logging.getLogger(name)
    
    # Allow overriding log level via environment variable
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    if hasattr(logging, log_level):
        logger.setLevel(getattr(logging, log_level))
    
    return logger

def ensure_directory(path: Path | str) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: Dict[str, Any], filepath: Path | str) -> None:
    """Save data to a JSON file."""
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(filepath: Path | str) -> Dict[str, Any]:
    """Load data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be used as a filename."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    return filename[:100]
