from __future__ import annotations

from typing import Any


def validate_openaq_metadata(
    metadata: dict[str, Any],
) -> None:
    """Validate OpenAQ sensor-selection and pagination metadata."""

    if not metadata.get("selected_sensors"):
        raise AssertionError("OpenAQ sensor selection metadata is missing.")

    if not metadata.get("pagination_pages"):
        raise AssertionError("OpenAQ pagination metadata is missing.")
