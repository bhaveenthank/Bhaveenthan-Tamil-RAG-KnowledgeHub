from __future__ import annotations

from typing import Any


def tamilvu_song_citation(record: dict[str, Any]) -> str:
    author = record.get("author") or record.get("nayanmar") or ""
    thirumurai = record.get("thirumurai") or record.get("canonical_title") or ""
    title = record.get("hymn_title") or record.get("title") or ""
    song_no = record.get("song_no") or record.get("verse_no") or ""
    parts = [part for part in [author, thirumurai, title] if part]
    prefix = ", ".join(parts)
    suffix = f"பாடல் {song_no}, TamilVU." if song_no else "TamilVU."
    return f"{prefix}, {suffix}" if prefix else suffix
