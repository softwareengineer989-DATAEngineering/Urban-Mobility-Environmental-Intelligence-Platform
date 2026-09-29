from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from urban_mobility.ingestion.metadata import (
    load_json,
    save_json,
    utc_now,
)
from urban_mobility.ingestion.noaa import acquire_noaa
from urban_mobility.ingestion.openaq import acquire_openaq
from urban_mobility.ingestion.taxi_zones import acquire_taxi_zones
from urban_mobility.ingestion.tlc import acquire_tlc

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = PROJECT_ROOT / "configs" / "datasets" / "phase1_sources.json"

MANIFEST_PATH = PROJECT_ROOT / "data" / "metadata" / "phase1_manifest.json"


def main() -> int:
    config = load_json(CONFIG_PATH)

    manifest: dict[str, Any] = {
        "phase": "phase1",
        "generated_at_utc": utc_now(),
        "window": config["window"],
        "sources": {},
    }

    acquire_tlc(
        config,
        manifest,
        PROJECT_ROOT,
    )

    acquire_noaa(
        config,
        manifest,
        PROJECT_ROOT,
    )

    acquire_taxi_zones(
        config,
        manifest,
        PROJECT_ROOT,
    )

    acquire_openaq(
        config,
        manifest,
        PROJECT_ROOT,
    )

    save_json(
        MANIFEST_PATH,
        manifest,
    )

    print("\n============================================================")
    print("PHASE 1 ACQUISITION COMPLETE")
    print("============================================================")
    print(f"Manifest: {MANIFEST_PATH}")
    print("Raw datasets were stored under data/raw/.")
    print("Raw datasets must NOT be committed to Git.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(
            "\nAcquisition cancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)
    except Exception as exc:
        print(
            f"\nPHASE 1 ACQUISITION FAILED: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
