from __future__ import annotations

from pathlib import Path
from typing import Any

from .download import download_file
from .metadata import utc_now


def acquire_tlc(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Acquire the configured NYC TLC Yellow Taxi files."""

    print("\n[1/4] Acquiring NYC TLC Yellow Taxi data...")

    entries: list[dict[str, Any]] = []

    for source_file in config["sources"]["tlc"]["files"]:
        destination = project_root / source_file["path"]

        print(f"  Downloading {source_file['month']}...")

        result = download_file(
            source_file["url"],
            destination,
            project_root,
        )

        result["month"] = source_file["month"]
        result["source"] = "NYC TLC Yellow Taxi"

        entries.append(result)

        print(f"  OK: {result['path']} ({result['size_bytes']:,} bytes)")

    manifest["sources"]["tlc"] = {
        "retrieved_at_utc": utc_now(),
        "files": entries,
    }
