from __future__ import annotations

from urban_mobility.config import require_openaq_api_key


def get_openaq_headers() -> dict[str, str]:
    """Return authenticated headers for OpenAQ API requests."""
    return {
        "X-API-Key": require_openaq_api_key(),
    }
