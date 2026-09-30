from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET = os.getenv("BUCKET") or os.getenv("S3_BUCKET_NAME")

CHECKSUM_MANIFEST_LOCAL = PROJECT_ROOT / "data" / "metadata" / "phase2_s3_checksum_manifest.json"

CHECKSUM_MANIFEST_S3_KEY = "metadata/checksums/phase2_s3_checksum_manifest.json"


EXPECTED_RAW_OBJECTS = {
    "raw/tlc/yellow/yellow_tripdata_2024-01.parquet",
    "raw/tlc/yellow/yellow_tripdata_2024-02.parquet",
    "raw/tlc/yellow/yellow_tripdata_2024-03.parquet",
    "raw/noaa/global_hourly/72503014732_2024_q1.csv",
    "raw/noaa/global_hourly/72505394728_2024_q1.csv",
    "raw/noaa/global_hourly/74486094789_2024_q1.csv",
    "raw/openaq/openaq_nyc_2024_q1.json",
    "raw/taxi_zones/taxi_zone_lookup.csv",
    "raw/taxi_zones/taxi_zones.zip",
}


EXPECTED_SOURCE_MARKERS = {
    "raw/tlc/_SOURCE_READY",
    "raw/noaa/_SOURCE_READY",
    "raw/openaq/_SOURCE_READY",
    "raw/taxi_zones/_SOURCE_READY",
}


EXPECTED_METADATA_OBJECTS = {
    "metadata/manifests/phase2_manifest.json",
    "metadata/manifests/project.json",
    "metadata/schemas/phase2_s3_layout.json",
}


EXPECTED_PREFIX_MARKERS = {
    "bronze/tlc/",
    "bronze/noaa/",
    "bronze/openaq/",
    "bronze/taxi_zones/",
    "silver/tlc/",
    "silver/noaa/",
    "silver/openaq/",
    "silver/taxi_zones/",
    "curated/mobility/",
    "curated/weather/",
    "curated/air_quality/",
    "curated/geospatial/",
    "metadata/schemas/",
    "metadata/manifests/",
    "metadata/checksums/",
    "checkpoints/tlc/",
    "checkpoints/noaa/",
    "checkpoints/openaq/",
    "checkpoints/taxi_zones/",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_s3_json(s3_client: Any, key: str) -> dict[str, Any]:
    response = s3_client.get_object(
        Bucket=BUCKET,
        Key=key,
        ChecksumMode="ENABLED",
    )

    body = response["Body"].read()

    if not body:
        fail(f"S3 metadata object is empty: {key}")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in S3 object {key}: {exc}")

    if not isinstance(payload, dict):
        fail(f"S3 metadata object must contain a JSON object: {key}")

    return payload


def hash_s3_object(
    s3_client: Any,
    key: str,
) -> dict[str, Any]:
    head = s3_client.head_object(
        Bucket=BUCKET,
        Key=key,
        ChecksumMode="ENABLED",
    )

    expected_size = head["ContentLength"]

    response = s3_client.get_object(
        Bucket=BUCKET,
        Key=key,
        ChecksumMode="ENABLED",
    )

    digest = hashlib.sha256()
    bytes_read = 0

    body = response["Body"]

    while True:
        chunk = body.read(8 * 1024 * 1024)

        if not chunk:
            break

        digest.update(chunk)
        bytes_read += len(chunk)

    body.close()

    if bytes_read != expected_size:
        fail(f"S3 object size mismatch for {key}: HEAD={expected_size}, READ={bytes_read}")

    checksum_fields = {name: value for name, value in head.items() if name.startswith("Checksum")}

    return {
        "key": key,
        "size_bytes": bytes_read,
        "sha256": digest.hexdigest(),
        "etag": head.get("ETag"),
        "last_modified": head.get("LastModified").isoformat() if head.get("LastModified") else None,
        "server_side_encryption": head.get("ServerSideEncryption"),
        "s3_checksums": checksum_fields,
    }


def validate_aws_identity(s3_client: Any) -> None:
    print("[1/7] Validating AWS identity...")

    sts = boto3.client(
        "sts",
        region_name=AWS_REGION,
    )

    identity = sts.get_caller_identity()

    account = identity["Account"]
    arn = identity["Arn"]

    print(f"  PASS account: {account}")
    print(f"  PASS caller:  {arn}")


def validate_bucket(s3_client: Any) -> None:
    print("\n[2/7] Validating S3 bucket...")

    response = s3_client.head_bucket(
        Bucket=BUCKET,
    )

    status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

    if status_code != 200:
        fail(f"S3 bucket validation failed: HTTP {status_code}")

    print(f"  PASS bucket: {BUCKET}")
    print(f"  PASS region: {AWS_REGION}")


def list_all_keys(s3_client: Any) -> set[str]:
    keys: set[str] = set()

    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(
        Bucket=BUCKET,
    ):
        for item in page.get("Contents", []):
            keys.add(item["Key"])

    return keys


def validate_layout(
    s3_client: Any,
    all_keys: set[str],
) -> None:
    print("\n[3/7] Validating S3 layout...")

    missing_markers = sorted(
        marker
        for marker in EXPECTED_PREFIX_MARKERS
        if marker not in all_keys and not any(key.startswith(marker) for key in all_keys)
    )

    if missing_markers:
        fail(
            "Required S3 prefixes are missing:\n"
            + "\n".join(f"  - {marker}" for marker in missing_markers)
        )

    print(f"  PASS required layout prefixes: {len(EXPECTED_PREFIX_MARKERS)}")


def validate_source_markers(
    s3_client: Any,
) -> None:
    print("\n[4/7] Validating source readiness markers...")

    for marker in sorted(EXPECTED_SOURCE_MARKERS):
        head = s3_client.head_object(
            Bucket=BUCKET,
            Key=marker,
        )

        size = head["ContentLength"]

        if size != 0:
            fail(f"Source readiness marker is not zero-byte: {marker} ({size} bytes)")

        print(f"  PASS {marker}")


def validate_raw_objects(
    s3_client: Any,
    all_keys: set[str],
) -> list[dict[str, Any]]:
    print("\n[5/7] Validating raw/source objects...")

    missing = sorted(EXPECTED_RAW_OBJECTS - all_keys)

    if missing:
        fail("Required raw objects are missing:\n" + "\n".join(f"  - {key}" for key in missing))

    unexpected_raw = sorted(
        key
        for key in all_keys
        if key.startswith("raw/")
        and key not in EXPECTED_RAW_OBJECTS
        and key not in EXPECTED_SOURCE_MARKERS
        and not key.endswith("/")
    )

    if unexpected_raw:
        print("  WARNING: additional raw objects detected:")

        for key in unexpected_raw:
            print(f"    {key}")

    results: list[dict[str, Any]] = []

    for key in sorted(EXPECTED_RAW_OBJECTS):
        result = hash_s3_object(
            s3_client,
            key,
        )

        if result["size_bytes"] <= 0:
            fail(f"Raw S3 object is empty: {key}")

        results.append(result)

        print(f"  PASS {key} ({result['size_bytes']:,} bytes)")

    return results


def validate_metadata(
    s3_client: Any,
    all_keys: set[str],
) -> dict[str, dict[str, Any]]:
    print("\n[6/7] Validating metadata objects...")

    missing = sorted(EXPECTED_METADATA_OBJECTS - all_keys)

    if missing:
        fail(
            "Required metadata objects are missing:\n" + "\n".join(f"  - {key}" for key in missing)
        )

    metadata_payloads: dict[str, dict[str, Any]] = {}

    for key in sorted(EXPECTED_METADATA_OBJECTS):
        payload = load_s3_json(
            s3_client,
            key,
        )

        head = s3_client.head_object(
            Bucket=BUCKET,
            Key=key,
            ChecksumMode="ENABLED",
        )

        encryption = head.get("ServerSideEncryption")

        if encryption != "AES256":
            fail(f"Metadata object is not SSE-S3 AES256 encrypted: {key}; actual={encryption}")

        metadata_payloads[key] = payload

        print(f"  PASS {key} (AES256, valid JSON)")

    return metadata_payloads


def write_and_upload_checksum_manifest(
    s3_client: Any,
    raw_results: list[dict[str, Any]],
) -> None:
    print("\n[7/7] Creating S3 raw checksum manifest...")

    CHECKSUM_MANIFEST_LOCAL.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "phase": "phase2",
        "name": "S3 Raw Object Integrity Manifest",
        "generated_at_utc": utc_now(),
        "bucket": BUCKET,
        "region": AWS_REGION,
        "algorithm": "SHA-256",
        "objects": raw_results,
    }

    CHECKSUM_MANIFEST_LOCAL.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    s3_client.upload_file(
        str(CHECKSUM_MANIFEST_LOCAL),
        BUCKET,
        CHECKSUM_MANIFEST_S3_KEY,
        ExtraArgs={
            "ServerSideEncryption": "AES256",
        },
    )

    head = s3_client.head_object(
        Bucket=BUCKET,
        Key=CHECKSUM_MANIFEST_S3_KEY,
        ChecksumMode="ENABLED",
    )

    if head["ContentLength"] <= 0:
        fail("Uploaded checksum manifest is empty.")

    if head.get("ServerSideEncryption") != "AES256":
        fail("Checksum manifest is not SSE-S3 AES256 encrypted.")

    print(f"  PASS uploaded: s3://{BUCKET}/{CHECKSUM_MANIFEST_S3_KEY}")

    print(f"  PASS local evidence: {CHECKSUM_MANIFEST_LOCAL}")


def main() -> int:
    print("=" * 60)
    print("PHASE 2 S3 RAW DATA + METADATA VALIDATION")
    print("=" * 60)

    if not BUCKET:
        print(
            "PHASE 2 VALIDATION FAILED",
            file=sys.stderr,
        )
        print(
            "Missing BUCKET or S3_BUCKET_NAME environment variable.",
            file=sys.stderr,
        )
        return 1

    try:
        s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
        )

        validate_aws_identity(s3_client)

        validate_bucket(s3_client)

        all_keys = list_all_keys(s3_client)

        validate_layout(
            s3_client,
            all_keys,
        )

        validate_source_markers(
            s3_client,
        )

        raw_results = validate_raw_objects(
            s3_client,
            all_keys,
        )

        validate_metadata(
            s3_client,
            all_keys,
        )

        write_and_upload_checksum_manifest(
            s3_client,
            raw_results,
        )

        print("\n" + "=" * 60)
        print("PHASE 2 VALIDATION PASSED")
        print("=" * 60)

        print(f"Raw objects validated: {len(raw_results)}")

        print(f"Source markers validated: {len(EXPECTED_SOURCE_MARKERS)}")

        print(f"Metadata objects validated: {len(EXPECTED_METADATA_OBJECTS)}")

        print(f"Checksum manifest: s3://{BUCKET}/{CHECKSUM_MANIFEST_S3_KEY}")

        return 0

    except (
        AssertionError,
        ClientError,
        BotoCoreError,
        OSError,
        ValueError,
    ) as exc:
        print("\n" + "=" * 60)
        print("PHASE 2 VALIDATION FAILED")
        print("=" * 60)
        print(f"Reason: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
