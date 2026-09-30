from __future__ import annotations

from urban_mobility.cloud.aws import (
    AWSSettings,
    create_aws_session,
    load_aws_settings,
)


def test_load_aws_settings(monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "urban-mobility-test-bucket")
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    settings = load_aws_settings()

    assert settings == AWSSettings(
        region="us-east-1",
        bucket_name="urban-mobility-test-bucket",
        profile_name=None,
    )


def test_load_aws_settings_with_profile(monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "urban-mobility-test-bucket")
    monkeypatch.setenv("AWS_PROFILE", "project2")

    settings = load_aws_settings()

    assert settings == AWSSettings(
        region="us-east-1",
        bucket_name="urban-mobility-test-bucket",
        profile_name="project2",
    )


def test_load_aws_settings_requires_region(monkeypatch) -> None:
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    monkeypatch.setenv("S3_BUCKET_NAME", "urban-mobility-test-bucket")

    try:
        load_aws_settings()
    except RuntimeError as exc:
        assert "AWS_REGION is not configured" in str(exc)
    else:
        raise AssertionError("Expected AWS region validation to fail")


def test_load_aws_settings_requires_bucket(monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    try:
        load_aws_settings()
    except RuntimeError as exc:
        assert "S3_BUCKET_NAME is not configured" in str(exc)
    else:
        raise AssertionError("Expected S3 bucket validation to fail")


def test_create_aws_session(monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "urban-mobility-test-bucket")
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    settings = load_aws_settings()
    session = create_aws_session(settings)

    assert session.region_name == "us-east-1"
