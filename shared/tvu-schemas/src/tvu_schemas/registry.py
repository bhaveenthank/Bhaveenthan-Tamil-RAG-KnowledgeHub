from __future__ import annotations

from pathlib import Path


def schema_path(name: str) -> Path:
    root = Path(__file__).resolve().parents[2] / "schemas"
    path = root / name
    if not path.is_file():
        raise FileNotFoundError(f"unknown schema: {name}")
    return path
