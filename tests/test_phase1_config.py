from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "datasets" / "phase1_sources.json"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_phase1_configuration_is_complete() -> None:
    config = load_config()

    assert config["phase"] == "phase1"

    assert config["window"]["start"] == "2024-01-01"
    assert config["window"]["end"] == "2024-03-31"

    sources = config["sources"]

    assert "tlc" in sources
    assert "noaa" in sources
    assert "openaq" in sources
    assert "taxi_zones" in sources

    assert len(sources["tlc"]["files"]) == 3

    assert len(sources["noaa"]["stations"]) == 3

    assert sources["openaq"]["api_base_url"] == ("https://api.openaq.org/v3")

    assert sources["openaq"]["max_sensors"] == 5

    assert sources["taxi_zones"]["lookup_url"].endswith("taxi_zone_lookup.csv")

    assert sources["taxi_zones"]["shapefile_url"].endswith("taxi_zones.zip")
