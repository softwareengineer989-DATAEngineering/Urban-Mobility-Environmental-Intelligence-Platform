from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

from .download import download_file
from .metadata import utc_now


def build_noaa_url(
    station_id: str,
    start_date: str,
    end_date: str,
) -> str:
    """Build the NOAA Global Hourly API URL."""

    params = {
        "dataset": "global-hourly",
        "stations": station_id,
        "startDate": start_date,
        "endDate": end_date,
        "format": "csv",
        "units": "metric",
    }

    return "https://www.ncei.noaa.gov/access/services/data/v1?" + urllib.parse.urlencode(params)


def acquire_noaa(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Acquire the configured NYC-area NOAA station data."""

    print("\n[2/4] Acquiring NOAA NYC-area hourly data...")

    window = config["window"]
    entries: list[dict[str, Any]] = []

    for station in config["sources"]["noaa"]["stations"]:
        url = build_noaa_url(
            station["station_id"],
            window["start"],
            window["end"],
        )

        destination = project_root / station["path"]

        print(f"  Downloading {station['name']} ({station['station_id']})...")

        result = download_file(
            url,
            destination,
            project_root,
        )

        result["station_id"] = station["station_id"]
        result["station_name"] = station["name"]
        result["source"] = "NOAA NCEI Global Hourly"

        entries.append(result)

        print(f"  OK: {result['path']} ({result['size_bytes']:,} bytes)")

    manifest["sources"]["noaa"] = {
        "retrieved_at_utc": utc_now(),
        "files": entries,
    }
