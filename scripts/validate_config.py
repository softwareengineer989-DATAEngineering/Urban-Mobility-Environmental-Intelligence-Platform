"""Validate the repository foundation configuration."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    PROJECT_ROOT / ".env.example",
    PROJECT_ROOT / "pyproject.toml",
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "src" / "urban_mobility" / "__init__.py",
]


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not path.is_file()]

    if missing:
        print("CONFIGURATION VALIDATION FAILED")
        for path in missing:
            print(f"Missing: {path}")
        return 1

    env_example = PROJECT_ROOT / ".env.example"

    required_environment_keys = [
        "PROJECT_NAME",
        "ENVIRONMENT",
        "LOG_LEVEL",
        "AWS_REGION",
        "S3_BUCKET_NAME",
        "NOAA_API_TOKEN",
        "OPENAQ_API_KEY",
    ]

    content = env_example.read_text(encoding="utf-8")

    missing_keys = [key for key in required_environment_keys if f"{key}=" not in content]

    if missing_keys:
        print("CONFIGURATION VALIDATION FAILED")
        for key in missing_keys:
            print(f"Missing environment key: {key}")
        return 1

    print("CONFIGURATION VALIDATION PASSED")
    print(f"Project root: {PROJECT_ROOT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
