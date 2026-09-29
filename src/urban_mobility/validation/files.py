from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON document."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_file(path: Path) -> None:
    """Require a non-empty file."""

    if not path.is_file():
        raise AssertionError(f"Required file missing: {path}")

    if path.stat().st_size <= 0:
        raise AssertionError(f"Required file is empty: {path}")
