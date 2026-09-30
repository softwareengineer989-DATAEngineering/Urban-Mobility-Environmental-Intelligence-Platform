from __future__ import annotations

import sys
from pathlib import Path

from urban_mobility.cloud.aws import (
    create_aws_session,
    create_s3_client,
    load_aws_settings,
    validate_aws_credentials,
    validate_s3_client,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("\n============================================================")
    print("PHASE 2 AWS CONFIGURATION VALIDATION")
    print("============================================================")

    settings = load_aws_settings()

    print(f"AWS region: {settings.region}")
    print(f"S3 bucket: {settings.bucket_name}")

    if settings.profile_name:
        print(f"AWS profile: {settings.profile_name}")
    else:
        print("AWS profile: default credential chain")

    session = create_aws_session(settings)

    print("\nValidating AWS credentials...")

    identity = validate_aws_credentials(session)

    print("AWS credentials: PASS")
    print(f"AWS account: {identity['account_id']}")
    print(f"AWS caller ARN: {identity['arn']}")
    print(f"AWS session region: {identity['region']}")

    print("\nValidating S3 client configuration...")

    validate_s3_client(session)
    create_s3_client(session)

    print("S3 client configuration: PASS")

    print("\n============================================================")
    print("PHASE 2 AWS CONFIGURATION VALIDATION PASSED")
    print("============================================================")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"\nPHASE 2 AWS CONFIGURATION VALIDATION FAILED: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
