from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .checksum import sha256_file

USER_AGENT = "urban-mobility-environmental-intelligence-platform/phase1"

DOWNLOAD_RETRY_COUNT = 8
DOWNLOAD_RETRY_BACKOFF_SECONDS = 5


def download_file(
    url: str,
    destination: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Download a source file atomically and return acquisition metadata."""

    destination.parent.mkdir(parents=True, exist_ok=True)

    last_error: Exception | None = None

    for attempt in range(1, DOWNLOAD_RETRY_COUNT + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT},
            )

            with urllib.request.urlopen(request, timeout=120) as response:
                content_length = response.headers.get("Content-Length")

                temporary = destination.with_suffix(destination.suffix + ".partial")

                with temporary.open("wb") as output:
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)

                temporary.replace(destination)

            size_bytes = destination.stat().st_size

            if size_bytes == 0:
                raise RuntimeError(f"Downloaded file is empty: {destination}")

            return {
                "url": url,
                "path": str(destination.relative_to(project_root)),
                "size_bytes": size_bytes,
                "content_length_header": content_length,
                "sha256": sha256_file(destination),
            }

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            RuntimeError,
        ) as exc:
            last_error = exc

            if attempt < DOWNLOAD_RETRY_COUNT:
                time.sleep(DOWNLOAD_RETRY_BACKOFF_SECONDS * attempt)

    raise RuntimeError(
        f"Failed to download {url} after {DOWNLOAD_RETRY_COUNT} attempts: {last_error}"
    )
