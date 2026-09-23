"""Tests for the Project 2 engineering foundation."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_directories_exist() -> None:
    required_directories = [
        ".github/workflows",
        "configs",
        "data/raw",
        "data/bronze",
        "data/silver",
        "data/curated",
        "docs",
        "infrastructure",
        "scripts",
        "src/urban_mobility",
        "tests",
    ]

    for directory in required_directories:
        assert (PROJECT_ROOT / directory).is_dir(), directory


def test_required_files_exist() -> None:
    required_files = [
        ".gitignore",
        ".env.example",
        "pyproject.toml",
        "README.md",
        "src/urban_mobility/__init__.py",
        "scripts/validate_config.py",
    ]

    for file_path in required_files:
        assert (PROJECT_ROOT / file_path).is_file(), file_path
