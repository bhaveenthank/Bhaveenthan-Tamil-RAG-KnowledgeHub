from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.pilot_ingest_category import jsonl_text, load_jsonl, write_once


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["schema_version"] = "website-corpus-v2"
    normalized["language"] = str(record.get("language") or "ta").strip()
    normalized["content_text"] = str(
        record.get("content_text") or record.get("verse_text") or ""
    ).strip()
    normalized["verse_text"] = str(record.get("verse_text") or "").strip()
    normalized["source_url"] = str(record.get("source_url") or "").strip()
    normalized["parser_family"] = str(
        record.get("parser_family")
        or record.get("source_metadata", {}).get("parser_family")
        or ""
    ).strip()
    normalized["source_metadata"] = dict(record.get("source_metadata") or {})
    if normalized.get("record_type") == "dictionary_entry":
        normalized["entry_headword"] = str(record.get("entry_headword") or "").strip()
        normalized["definition"] = str(
            record.get("definition") or normalized["content_text"]
        ).strip()
        normalized["part_of_speech"] = str(
            record.get("part_of_speech") or ""
        ).strip()
        normalized["content_text"] = normalized["definition"]
    if normalized.get("category_id") == "sangam_literature":
        for field in (
            "poem_no",
            "thinai",
            "thurai",
            "colophon",
            "author",
            "commentary_url",
        ):
            normalized[field] = str(record.get(field) or "").strip()
        normalized["content_text"] = normalized["verse_text"]
    if normalized.get("category_id") == "grammar":
        for field in (
            "rule_no",
            "rule_text",
            "explanation_text",
            "section_id",
            "chapter_id",
            "commentary_url",
        ):
            normalized[field] = str(record.get(field) or "").strip()
        normalized["content_text"] = normalized["rule_text"]
    return normalized


def normalize_category(
    category_id: str,
    *,
    base_dir: Path = Path("."),
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> tuple[list[dict[str, Any]], Path, str]:
    source = input_path or (
        base_dir / "data/processed/pilot_categories" / category_id / "records.jsonl"
    )
    output = output_path or (
        base_dir
        / "data/processed/normalized_categories"
        / f"{category_id}_normalized.jsonl"
    )
    records = [normalize_record(record) for record in load_jsonl(source, 10)]
    status = write_once(output, jsonl_text(records))
    return records, output, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize a bounded category pilot to schema v2.")
    parser.add_argument("--category-id", required=True)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        records, output, status = normalize_category(
            args.category_id,
            base_dir=args.base_dir,
            input_path=args.input,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Normalized records: {len(records)}")
    print(f"Output: {output}")
    print(f"Write status: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
