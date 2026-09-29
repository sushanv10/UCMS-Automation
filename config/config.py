"""
Configuration module for UCMS automation framework.
Loads settings from environment variables / .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env" )


class Config:
    """Central configuration class."""

    # Application
    BASE_URL: str = os.getenv("BASE_URL", "https://ucms.dev.geniussystems.com.np")
    LOGIN_URL: str = f"{BASE_URL}/login"
    DASHBOARD_URL: str = f"{BASE_URL}/dashboard" 
    NETWORK_EXPLORER_URL: str = f"{BASE_URL}/map"
    PROTECTED_URL: str = f"{BASE_URL}/map" 

    # Credentials
    VALID_USERNAME: str = os.getenv("VALID_USERNAME")
    VALID_PASSWORD: str = os.getenv("VALID_PASSWORD")

    # User display info (from profile button)
    USER_FULL_NAME: str = os.getenv("USER_FULL_NAME", "Sushan Vaidya")
    USER_INITIALS: str = os.getenv("USER_INITIALS", "SV")

    # Browser / Playwright
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30000"))
    VIEWPORT = {"width": 1200, "height": 800}
    # TIMEOUT_MS = int(os.getenv("UCMS_TIMEOUT_MS", "15000"))

    # Paths
    SCREENSHOTS_DIR: Path = PROJECT_ROOT / "screenshots"
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"


    @classmethod
    def ensure_dirs(cls) -> None:
        """Create output directories if they do not exist."""
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def has_valid_credentials(cls) -> bool:
        return bool(cls.VALID_USERNAME and cls.VALID_PASSWORD)
