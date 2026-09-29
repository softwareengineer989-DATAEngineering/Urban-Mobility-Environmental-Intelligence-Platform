from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .api import validate_openaq_metadata
from .checksums import verify_checksum
from .files import load_json, require_file
from .schemas import (
    validate_noaa_schema,
    validate_openaq_schema,
    validate_taxi_zone_geometry,
    validate_taxi_zone_lookup_schema,
    validate_tlc_schema,
)


def validate_tlc(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Validate TLC files."""

    print("\n[1/4] Validating TLC...")

    required = set(config["sources"]["tlc"]["required_columns"])

    for entry in manifest["sources"]["tlc"]["files"]:
        path = project_root / entry["path"]

        require_file(path)

        verify_checksum(
            path,
            entry["sha256"],
            "TLC",
        )

        parquet = pq.ParquetFile(path)

        validate_tlc_schema(
            parquet.schema_arrow.names,
            required,
            path,
        )

        metadata = parquet.metadata

        if metadata.num_rows <= 0:
            raise AssertionError(f"TLC contains zero records: {path}")

        sample_columns = [
            "VendorID",
            "tpep_pickup_datetime",
            "tpep_dropoff_datetime",
            "PULocationID",
            "DOLocationID",
            "total_amount",
        ]

        sample = parquet.read(
            columns=sample_columns,
        ).slice(0, 5)

        if sample.num_rows == 0:
            raise AssertionError(f"TLC representative-record validation failed: {path}")

        print(
            f"  PASS {entry['month']}: "
            f"{metadata.num_rows:,} rows, "
            f"{len(parquet.schema_arrow.names)} columns"
        )


def validate_noaa(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Validate NOAA files."""

    print("\n[2/4] Validating NOAA...")

    for entry in manifest["sources"]["noaa"]["files"]:
        path = project_root / entry["path"]

        require_file(path)

        verify_checksum(
            path,
            entry["sha256"],
            "NOAA",
        )

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            validate_noaa_schema(
                reader.fieldnames,
                path,
            )

            rows = []

            for row_number, row in enumerate(reader):
                rows.append(row)

                if row_number >= 4:
                    break

        if not rows:
            raise AssertionError(f"NOAA contains zero representative records: {path}")

        for row in rows:
            if not row["STATION"]:
                raise AssertionError(f"NOAA station is empty: {path}")

            if not row["DATE"]:
                raise AssertionError(f"NOAA date is empty: {path}")

        print(f"  PASS {entry['station_id']} ({entry['station_name']})")


def validate_openaq(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Validate OpenAQ output, metadata and pagination evidence."""

    print("\n[3/4] Validating OpenAQ...")

    entry = manifest["sources"]["openaq"]

    path = project_root / entry["path"]

    require_file(path)

    verify_checksum(
        path,
        entry["sha256"],
        "OpenAQ",
    )

    payload = load_json(path)

    metadata = payload.get("metadata")
    results = payload.get("results")

    validate_openaq_schema(
        metadata,
        results,
    )

    validate_openaq_metadata(
        metadata,
    )

    required_result_keys = {
        "value",
        "parameter",
        "period",
    }

    for result in results[:10]:
        missing = required_result_keys - result.keys()

        if missing:
            raise AssertionError(f"OpenAQ record missing fields: {sorted(missing)}")

    print(f"  PASS: {len(results):,} records from {len(metadata['selected_sensors'])} sensors")

    print(
        "  Pagination evidence:",
        metadata["pagination_pages"],
    )


def validate_taxi_zones(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Validate taxi-zone lookup and geometry data."""

    print("\n[4/4] Validating taxi-zone reference data...")

    source = config["sources"]["taxi_zones"]

    lookup_path = project_root / source["lookup_path"]

    zip_path = project_root / source["shapefile_path"]

    require_file(lookup_path)
    require_file(zip_path)

    lookup_manifest = manifest["sources"]["taxi_zones"]["lookup"]

    zip_manifest = manifest["sources"]["taxi_zones"]["shapefile"]

    verify_checksum(
        lookup_path,
        lookup_manifest["sha256"],
        "Taxi-zone lookup",
    )

    verify_checksum(
        zip_path,
        zip_manifest["sha256"],
        "Taxi-zone shapefile",
    )

    with lookup_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        validate_taxi_zone_lookup_schema(
            reader.fieldnames,
        )

        sample_rows = []

        for index, row in enumerate(reader):
            sample_rows.append(row)

            if index >= 4:
                break

    if len(sample_rows) < 5:
        raise AssertionError("Taxi-zone lookup representative-record validation failed.")

    with zipfile.ZipFile(zip_path) as archive:
        members = {Path(name).suffix.lower() for name in archive.namelist()}

        validate_taxi_zone_geometry(members)

    print("  PASS: lookup schema, representative rows, and geometry archive validated.")
