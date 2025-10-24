"""API router for configuration and themes."""

import os
from fastapi import APIRouter
from api.schemas.job_schema import ThemesResponse, ThemeInfo, ConfigCheckResponse

router = APIRouter(prefix="/api/v1", tags=["config"])

# Available themes (from themes.md)
THEMES = [
    ThemeInfo(
        name="Modern Professional",
        description="Clean design with blue accents and professional typography",
        preview_url="/api/v1/theme-previews/modern-professional.png"
    ),
    ThemeInfo(
        name="Dark Mode",
        description="Dark background with neon highlights and modern aesthetics",
        preview_url="/api/v1/theme-previews/dark-mode.png"
    ),
    ThemeInfo(
        name="Vibrant Creative",
        description="Bold colors and dynamic layouts for creative presentations",
        preview_url="/api/v1/theme-previews/vibrant-creative.png"
    ),
    ThemeInfo(
        name="Minimal Clean",
        description="Minimalist design with plenty of white space",
        preview_url="/api/v1/theme-previews/minimal-clean.png"
    ),
    ThemeInfo(
        name="Corporate Blue",
        description="Traditional corporate style with navy blue theme",
        preview_url="/api/v1/theme-previews/corporate-blue.png"
    )
]


@router.get("/themes", response_model=ThemesResponse)
async def list_themes():
    """
    List available presentation themes.

    Returns:
        ThemesResponse with list of available themes
    """
    return ThemesResponse(themes=THEMES)


@router.post("/check-config", response_model=ConfigCheckResponse)
async def check_configuration():
    """
    Verify API keys and configuration (admin endpoint).

    Returns:
        ConfigCheckResponse with configuration status
    """
    return ConfigCheckResponse(
        soniox_configured=bool(os.getenv("SONIOX_API_KEY")),
        anthropic_configured=bool(os.getenv("CONTENT_ANTHROPIC_API_KEY")),
        unsplash_configured=bool(os.getenv("UNSPLASH_ACCESS_KEY")),
        playwright_installed=True  # Assume installed in container
    )
