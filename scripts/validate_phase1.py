from __future__ import annotations

import sys
from pathlib import Path

from urban_mobility.ingestion.metadata import load_json
from urban_mobility.validation.records import (
    validate_noaa,
    validate_openaq,
    validate_taxi_zones,
    validate_tlc,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = PROJECT_ROOT / "configs" / "datasets" / "phase1_sources.json"

MANIFEST_PATH = PROJECT_ROOT / "data" / "metadata" / "phase1_manifest.json"


def main() -> int:
    config = load_json(CONFIG_PATH)
    manifest = load_json(MANIFEST_PATH)

    validate_tlc(
        config,
        manifest,
        PROJECT_ROOT,
    )

    validate_noaa(
        config,
        manifest,
        PROJECT_ROOT,
    )

    validate_openaq(
        config,
        manifest,
        PROJECT_ROOT,
    )

    validate_taxi_zones(
        config,
        manifest,
        PROJECT_ROOT,
    )

    print("\n============================================================")
    print("PHASE 1 DATASET VALIDATION PASSED")
    print("============================================================")
    print("All four approved data sources passed validation.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"\nPHASE 1 VALIDATION FAILED: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
