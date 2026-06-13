from __future__ import annotations

from typing import Any


def require_fields(record: dict[str, Any], required: dict[str, type]) -> list[str]:
    errors = []
    for field, expected_type in required.items():
        if field not in record:
            errors.append(f"missing field: {field}")
        elif not isinstance(record[field], expected_type):
            errors.append(
                f"invalid field type for {field}: expected {expected_type.__name__}, "
                f"got {type(record[field]).__name__}"
            )
    return errors
