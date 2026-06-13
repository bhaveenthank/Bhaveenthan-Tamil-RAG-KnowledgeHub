from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_fields(schema: dict[str, Any], record: dict[str, Any]) -> list[str]:
    errors = []
    for field in schema.get("required", []):
        if field not in record:
            errors.append(f"missing required field: {field}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an artifact manifest against a schema.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("shared/tvu-schemas/schemas/artifact_manifest.schema.json"),
    )
    args = parser.parse_args(argv)

    schema = load_json(args.schema)
    manifest = load_json(args.manifest)
    errors = validate_required_fields(schema, manifest)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {args.manifest} against {args.schema}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
