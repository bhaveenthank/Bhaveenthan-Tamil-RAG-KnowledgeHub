from __future__ import annotations

import re

ID_PART_RE = re.compile(r"[^0-9A-Za-z_]+")


def stable_id(*parts: object) -> str:
    cleaned = []
    for part in parts:
        value = ID_PART_RE.sub("_", str(part).strip()).strip("_").lower()
        if value:
            cleaned.append(value)
    return "_".join(cleaned)
