from __future__ import annotations

from pathlib import Path
from typing import Any

from .download import download_file
from .metadata import utc_now


def acquire_taxi_zones(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Acquire the NYC taxi-zone lookup and geometry archive."""

    print("\n[3/4] Acquiring NYC taxi-zone reference data...")

    source = config["sources"]["taxi_zones"]

    lookup_destination = project_root / source["lookup_path"]
    shapefile_destination = project_root / source["shapefile_path"]

    print("  Downloading taxi-zone lookup CSV...")

    lookup_result = download_file(
        source["lookup_url"],
        lookup_destination,
        project_root,
    )

    print("  Downloading taxi-zone shapefile ZIP...")

    shapefile_result = download_file(
        source["shapefile_url"],
        shapefile_destination,
        project_root,
    )

    manifest["sources"]["taxi_zones"] = {
        "retrieved_at_utc": utc_now(),
        "lookup": lookup_result,
        "shapefile": shapefile_result,
    }

    print("  Taxi-zone reference data acquired.")
