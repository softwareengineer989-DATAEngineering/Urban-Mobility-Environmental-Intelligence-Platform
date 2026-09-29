from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")


def require_openaq_api_key() -> str:
    """Return the OpenAQ API key or fail with a clear configuration error."""
    if not OPENAQ_API_KEY:
        raise RuntimeError("OPENAQ_API_KEY is not configured. Add it to the project's .env file.")

    return OPENAQ_API_KEY
