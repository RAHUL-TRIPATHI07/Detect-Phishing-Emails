import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:5500"
)

GMAIL_REDIRECT_URI = os.getenv(
    "GMAIL_REDIRECT_URI",
    "http://127.0.0.1:8000/auth/gmail/callback"
)

GOOGLE_CREDENTIALS_FILE = Path(
    os.getenv(
        "GOOGLE_CREDENTIALS_FILE",
        str(PROJECT_ROOT / "secrets" / "credentials.json")
    )
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./sentinel.db"
)

TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY")


def validate_config():
    """Validate configuration required by the application."""

    if not SESSION_SECRET_KEY:
        raise ValueError(
            "SESSION_SECRET_KEY is not configured."
        )

    if not GOOGLE_CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Google OAuth credentials not found: "
            f"{GOOGLE_CREDENTIALS_FILE}"
        )

    if ENVIRONMENT == "production" and not TOKEN_ENCRYPTION_KEY:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY is required in production."
        )