from __future__ import annotations

import re
import unicodedata

TAMIL_BLOCK = re.compile(r"[\u0B80-\u0BFF]")


def normalize_tamil_text(text: str, form: str = "NFC") -> str:
    normalized = unicodedata.normalize(form, text)
    lines = [" ".join(line.split()) for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line)


def tamil_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    tamil_count = len(TAMIL_BLOCK.findall("".join(letters)))
    return tamil_count / len(letters)

