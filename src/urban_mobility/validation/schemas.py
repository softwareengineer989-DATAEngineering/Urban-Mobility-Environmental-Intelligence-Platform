from __future__ import annotations

from pathlib import Path
from typing import Iterable


def validate_tlc_schema(
    columns: Iterable[str],
    required: set[str],
    path: Path,
) -> None:
    """Validate the required TLC Parquet columns."""

    actual_columns = set(columns)
    missing = required - actual_columns

    if missing:
        raise AssertionError(f"TLC schema missing columns in {path}: {sorted(missing)}")


def validate_noaa_schema(
    fieldnames: list[str] | None,
    path: Path,
) -> None:
    """Validate the required NOAA CSV columns."""

    if not fieldnames:
        raise AssertionError(f"NOAA CSV has no header: {path}")

    required_columns = {
        "STATION",
        "DATE",
        "NAME",
    }

    columns = set(fieldnames)

    missing = required_columns - columns

    if missing:
        raise AssertionError(f"NOAA schema missing columns: {sorted(missing)}")


def validate_openaq_schema(
    metadata: object,
    results: object,
) -> None:
    """Validate the OpenAQ top-level JSON structure."""

    if not isinstance(metadata, dict):
        raise AssertionError("OpenAQ metadata section is missing.")

    if not isinstance(results, list):
        raise AssertionError("OpenAQ results must be a list.")

    if not results:
        raise AssertionError("OpenAQ returned zero records.")


def validate_taxi_zone_lookup_schema(
    fieldnames: list[str] | None,
) -> None:
    """Validate the taxi-zone lookup CSV schema."""

    if not fieldnames:
        raise AssertionError("Taxi-zone lookup has no header.")

    normalized = {field.strip().lower() for field in fieldnames}

    required = {
        "locationid",
        "borough",
        "zone",
    }

    missing = required - normalized

    if missing:
        raise AssertionError(f"Taxi-zone lookup missing columns: {sorted(missing)}")


def validate_taxi_zone_geometry(
    members: set[str],
) -> None:
    """Validate the required shapefile members."""

    required_geometry_members = {
        ".shp",
        ".dbf",
        ".shx",
    }

    missing = required_geometry_members - members

    if missing:
        raise AssertionError(f"Taxi-zone geometry archive missing: {sorted(missing)}")
