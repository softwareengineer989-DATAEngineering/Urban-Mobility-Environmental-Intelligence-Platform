from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from urban_mobility.openaq import get_openaq_headers

from .checksum import sha256_file
from .http_client import api_get_json
from .metadata import save_json, utc_now

OPENAQ_CHUNK_DAYS = 7
OPENAQ_PAGE_LIMIT = 1000
OPENAQ_MAX_PAGES_PER_WINDOW = 100


def _parse_utc_datetime(value: str) -> datetime:
    """Parse an ISO-8601 datetime and normalize it to UTC."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _format_utc_datetime(value: datetime) -> str:
    """Format a datetime in the UTC representation expected by OpenAQ."""

    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def select_openaq_sensors(
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Select deterministic OpenAQ sensors within the configured scope."""

    source = config["sources"]["openaq"]

    bbox = ",".join(str(value) for value in source["bbox"])

    query = {
        "bbox": bbox,
        "iso": "US",
        "limit": 1000,
        "page": 1,
        "order_by": "id",
        "sort_order": "asc",
    }

    url = f"{source['api_base_url']}/locations?{urlencode(query)}"

    payload = api_get_json(
        url,
        headers=get_openaq_headers(),
    )

    locations = payload.get("results", [])

    wanted_parameters = set(source["parameters"])

    candidates: list[dict[str, Any]] = []

    for location in locations:
        location_id = location.get("id")
        location_name = location.get("name")

        for sensor in location.get("sensors", []):
            parameter = sensor.get("parameter") or {}
            parameter_name = parameter.get("name")

            if parameter_name not in wanted_parameters:
                continue

            candidates.append(
                {
                    "location_id": location_id,
                    "location_name": location_name,
                    "sensor_id": sensor.get("id"),
                    "parameter": parameter_name,
                    "units": parameter.get("units"),
                    "datetime_first": sensor.get("datetimeFirst"),
                    "datetime_last": sensor.get("datetimeLast"),
                }
            )

    window_start = _parse_utc_datetime(config["window"]["start"])

    window_end = _parse_utc_datetime(config["window"]["end"])

    if len(config["window"]["end"]) == 10:
        window_end = window_end.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0,
        )

    def coverage_score(
        candidate: dict[str, Any],
    ) -> float:
        first_value = candidate.get("datetime_first")

        last_value = candidate.get("datetime_last")

        try:
            first_dt = _parse_utc_datetime(first_value) if first_value else window_start
        except (TypeError, ValueError):
            first_dt = window_start

        try:
            last_dt = _parse_utc_datetime(last_value) if last_value else window_end
        except (TypeError, ValueError):
            last_dt = window_end

        overlap_start = max(
            first_dt,
            window_start,
        )

        overlap_end = min(
            last_dt,
            window_end,
        )

        if overlap_end < overlap_start:
            return -1.0

        return (overlap_end - overlap_start).total_seconds()

    candidates = [
        candidate
        for candidate in candidates
        if candidate["sensor_id"] is not None and coverage_score(candidate) >= 0
    ]

    candidates.sort(
        key=lambda item: (
            item["parameter"],
            -coverage_score(item),
            item["sensor_id"] or 0,
        )
    )

    selected: list[dict[str, Any]] = []
    parameters_seen: set[str] = set()

    for candidate in candidates:
        parameter = candidate["parameter"]

        if parameter in parameters_seen:
            continue

        selected.append(candidate)
        parameters_seen.add(parameter)

        if len(selected) >= source["max_sensors"]:
            break

    return selected


def fetch_openaq_sensor_hours(
    config: dict[str, Any],
    sensor_id: int,
) -> tuple[list[dict[str, Any]], int]:
    """
    Fetch OpenAQ hourly measurements using bounded UTC windows.

    Each request uses OpenAQ v3 datetime_from/datetime_to
    filters and retains pagination inside each bounded window.
    """

    source = config["sources"]["openaq"]

    api_base_url = source["api_base_url"].rstrip("/")

    window = config["window"]

    window_start = _parse_utc_datetime(window["start"])

    window_end = _parse_utc_datetime(window["end"])

    if len(window["end"]) == 10:
        window_end = window_end.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0,
        )

    all_results: list[dict[str, Any]] = []
    total_pages = 0

    current_start = window_start

    while current_start <= window_end:
        current_end = min(
            current_start + timedelta(days=OPENAQ_CHUNK_DAYS) - timedelta(seconds=1),
            window_end,
        )

        page = 1
        window_results = 0

        print(
            f"sensor={sensor_id}, "
            f"window={_format_utc_datetime(current_start)}"
            f"→{_format_utc_datetime(current_end)}"
        )

        while True:
            query = urlencode(
                {
                    "datetime_from": _format_utc_datetime(current_start),
                    "datetime_to": _format_utc_datetime(current_end),
                    "limit": OPENAQ_PAGE_LIMIT,
                    "page": page,
                }
            )

            url = f"{api_base_url}/sensors/{sensor_id}/hours?{query}"

            payload = api_get_json(
                url,
                headers=get_openaq_headers(),
            )

            results = payload.get(
                "results",
                [],
            )

            if not results:
                break

            all_results.extend(results)

            window_results += len(results)
            total_pages += 1

            print(
                f"sensor={sensor_id}, "
                f"window={_format_utc_datetime(current_start)}"
                f"→{_format_utc_datetime(current_end)}, "
                f"page={page}, "
                f"records={len(results)}"
            )

            meta = payload.get("meta", {})
            found = meta.get("found")

            if found is not None:
                try:
                    found = int(found)
                except (TypeError, ValueError):
                    found = None

            if found is not None:
                if page * OPENAQ_PAGE_LIMIT >= found:
                    break

            elif len(results) < OPENAQ_PAGE_LIMIT:
                break

            page += 1

            if page > OPENAQ_MAX_PAGES_PER_WINDOW:
                raise RuntimeError(
                    "OpenAQ pagination safety limit exceeded "
                    f"for sensor {sensor_id}, "
                    f"window={_format_utc_datetime(current_start)}"
                    f"→{_format_utc_datetime(current_end)}"
                )

        print(
            f"    OK: sensor={sensor_id}, "
            f"window_records={window_results:,}, "
            f"pages={page if window_results else 0}"
        )

        current_start = current_end + timedelta(seconds=1)

    return all_results, total_pages


def acquire_openaq(
    config: dict[str, Any],
    manifest: dict[str, Any],
    project_root: Path,
) -> None:
    """Acquire bounded OpenAQ NYC-area measurements."""

    print("\n[4/4] Acquiring OpenAQ NYC-area measurements...")

    get_openaq_headers()

    source = config["sources"]["openaq"]

    selected_sensors = select_openaq_sensors(config)

    if not selected_sensors:
        raise RuntimeError(
            "No OpenAQ sensors matching the approved NYC bbox and parameter scope were found."
        )

    print("\n  Selected OpenAQ sensors:")

    for sensor in selected_sensors:
        print(f"    {sensor['sensor_id']} | {sensor['parameter']} | {sensor['location_name']}")

    all_results: list[dict[str, Any]] = []
    pagination: dict[str, int] = {}

    for sensor in selected_sensors:
        sensor_results, pages = fetch_openaq_sensor_hours(
            config,
            int(sensor["sensor_id"]),
        )

        for result in sensor_results:
            result["_sensor_id"] = sensor["sensor_id"]
            result["_location_id"] = sensor["location_id"]
            result["_location_name"] = sensor["location_name"]

        all_results.extend(sensor_results)

        pagination[str(sensor["sensor_id"])] = pages

    output = {
        "metadata": {
            "source": "OpenAQ",
            "api_base_url": source["api_base_url"],
            "retrieved_at_utc": utc_now(),
            "window": config["window"],
            "bbox": source["bbox"],
            "selected_sensors": selected_sensors,
            "pagination_pages": pagination,
            "record_count": len(all_results),
        },
        "results": all_results,
    }

    destination = project_root / source["path"]

    save_json(
        destination,
        output,
    )

    manifest["sources"]["openaq"] = {
        "retrieved_at_utc": output["metadata"]["retrieved_at_utc"],
        "path": str(destination.relative_to(project_root)),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "selected_sensors": selected_sensors,
        "pagination_pages": pagination,
        "record_count": len(all_results),
    }

    print(f"  OK: {destination.relative_to(project_root)} ({len(all_results):,} records)")
