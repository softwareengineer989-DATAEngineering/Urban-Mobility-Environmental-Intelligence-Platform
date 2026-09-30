from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class AWSSettings:
    """Runtime AWS configuration for the Project 2 cloud layer."""

    region: str
    bucket_name: str
    profile_name: str | None = None


def load_aws_settings() -> AWSSettings:
    """Load and validate AWS/S3 configuration from environment variables."""

    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    profile_name = os.getenv("AWS_PROFILE")

    if not region:
        raise RuntimeError(
            "AWS_REGION is not configured. Set AWS_REGION in the project's .env file."
        )

    if not bucket_name:
        raise RuntimeError(
            "S3_BUCKET_NAME is not configured. Set S3_BUCKET_NAME in the project's .env file."
        )

    return AWSSettings(
        region=region.strip(),
        bucket_name=bucket_name.strip(),
        profile_name=profile_name.strip() if profile_name else None,
    )


def create_aws_session(settings: AWSSettings | None = None) -> boto3.Session:
    """Create a boto3 session using environment/profile-based credentials."""

    resolved_settings = settings or load_aws_settings()

    session_kwargs: dict[str, str] = {
        "region_name": resolved_settings.region,
    }

    if resolved_settings.profile_name:
        session_kwargs["profile_name"] = resolved_settings.profile_name

    return boto3.Session(**session_kwargs)


def create_s3_client(
    session: boto3.Session | None = None,
):
    """Create an S3 client using the configured AWS session."""

    resolved_session = session or create_aws_session()

    return resolved_session.client("s3")


def validate_aws_credentials(
    session: boto3.Session | None = None,
) -> dict[str, str]:
    """Validate that the configured AWS credentials can authenticate."""

    resolved_session = session or create_aws_session()

    credentials = resolved_session.get_credentials()

    if credentials is None:
        raise NoCredentialsError()

    sts_client = resolved_session.client("sts")
    identity = sts_client.get_caller_identity()

    account_id = identity.get("Account")
    arn = identity.get("Arn")
    user_id = identity.get("UserId")

    if not account_id or not arn or not user_id:
        raise RuntimeError("AWS credential validation returned an incomplete caller identity.")

    return {
        "account_id": account_id,
        "arn": arn,
        "user_id": user_id,
        "region": resolved_session.region_name or "",
    }


def validate_s3_client(
    session: boto3.Session | None = None,
) -> None:
    """Validate that an S3 client can be constructed."""

    resolved_session = session or create_aws_session()

    try:
        client = resolved_session.client("s3")
        if client.meta.region_name != resolved_session.region_name:
            raise RuntimeError("S3 client region does not match the configured AWS session region.")
    except (BotoCoreError, ValueError) as exc:
        raise RuntimeError("Failed to initialize the configured S3 client.") from exc
