from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def verify_checksum(
    path: Path,
    expected: str,
    label: str,
) -> None:
    """Verify a file against its expected SHA-256 checksum."""

    actual = sha256_file(path)

    if actual != expected:
        raise AssertionError(f"{label} checksum mismatch: {path}")
