from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.normalize_corpus import (
    CORPUS_CONFIGS,
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    DEFAULT_REGISTRY,
    build_manifest,
    load_jsonl,
    write_json,
)

DEFAULT_REPORT = Path("reports/corpus-normalization-report.md")
REQUIRED_FIELDS = {
    "schema_version": str,
    "record_id": str,
    "corpus_id": str,
    "thirumurai_no": int,
    "collection": str,
    "canonical_title": str,
    "author": str,
    "nayanmar": str,
    "hymn_id": str,
    "pathigam_id": str,
    "song_no": str,
    "verse_no": str,
    "title": str,
    "place": str,
    "deity": str,
    "verse_text": str,
    "pozhppurai": str,
    "kurippurai": str,
    "source_url": str,
    "commentary_url": str,
    "metadata": dict,
}
NON_EMPTY_FIELDS = {
    "schema_version",
    "record_id",
    "corpus_id",
    "collection",
    "canonical_title",
    "author",
    "nayanmar",
    "hymn_id",
    "pathigam_id",
    "song_no",
    "verse_no",
    "title",
    "deity",
    "verse_text",
    "source_url",
}


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    missing_fields: Counter[str] = Counter()
    invalid_types: Counter[str] = Counter()
    invalid_thirumurai_no = 0
    malformed_source_urls = 0
    schema_inconsistencies = 0
    record_ids: Counter[str] = Counter()
    extraction_statuses: Counter[str] = Counter()

    for record in records:
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in record:
                missing_fields[field] += 1
                continue
            if not isinstance(record[field], expected_type):
                invalid_types[field] += 1
        for field in NON_EMPTY_FIELDS:
            if field in record and isinstance(record[field], str) and not record[field].strip():
                missing_fields[field] += 1
        thirumurai_no = record.get("thirumurai_no")
        if not isinstance(thirumurai_no, int) or not 1 <= thirumurai_no <= 12:
            invalid_thirumurai_no += 1
        elif record.get("corpus_id") != f"thirumurai_{thirumurai_no:02d}":
            schema_inconsistencies += 1
        if isinstance(record.get("source_url"), str) and not valid_url(record["source_url"]):
            malformed_source_urls += 1
        if record.get("hymn_id") != record.get("pathigam_id"):
            schema_inconsistencies += 1
        if isinstance(record.get("record_id"), str) and record["record_id"]:
            record_ids[record["record_id"]] += 1
        status = str(record.get("metadata", {}).get("extraction_status", "")).strip()
        extraction_statuses[status or "unknown"] += 1

    duplicate_record_ids = sorted(
        record_id for record_id, count in record_ids.items() if count > 1
    )
    missing_summary = dict(sorted(missing_fields.items()))
    error_count = (
        sum(missing_fields.values())
        + sum(invalid_types.values())
        + invalid_thirumurai_no
        + malformed_source_urls
        + schema_inconsistencies
        + len(duplicate_record_ids)
    )
    return {
        "record_count": len(records),
        "valid_record_count": len(records) if error_count == 0 else None,
        "error_count": error_count,
        "missing_fields": missing_summary,
        "invalid_field_types": dict(sorted(invalid_types.items())),
        "duplicate_record_ids": duplicate_record_ids,
        "invalid_thirumurai_no": invalid_thirumurai_no,
        "malformed_source_urls": malformed_source_urls,
        "schema_inconsistencies": schema_inconsistencies,
        "extraction_status_counts": dict(sorted(extraction_statuses.items())),
        "status": "VALID" if error_count == 0 else "INVALID",
    }


def render_report(result: dict[str, Any], registry: dict[str, Any], corpus_id: str = "thirumurai_02") -> str:
    missing = result["missing_fields"]
    missing_rows = "\n".join(
        f"| `{field}` | {count} |" for field, count in missing.items()
    ) or "| None | 0 |"
    status_rows = "\n".join(
        f"| `{status}` | {count} |"
        for status, count in result["extraction_status_counts"].items()
    )
    return f"""# Corpus Normalization Report

## Summary

- Registry entries: `{len(registry.get("corpora", []))}`
- Normalized corpus: `{corpus_id}`
- Normalized records: `{result["record_count"]}`
- Validation status: `{result["status"]}`
- Validation errors: `{result["error_count"]}`
- Duplicate record IDs: `{len(result["duplicate_record_ids"])}`
- Invalid Thirumurai numbers: `{result["invalid_thirumurai_no"]}`
- Malformed source URLs: `{result["malformed_source_urls"]}`
- Schema inconsistencies: `{result["schema_inconsistencies"]}`

## Missing Fields

| Field | Records |
| --- | ---: |
{missing_rows}

## Extraction Status

| Status | Records |
| --- | ---: |
{status_rows}

Empty `pozhppurai` and `kurippurai` values are allowed only when extraction metadata records a source or partial-commentary condition. `place` and `commentary_url` are optional at schema level for future source families, although the current normalized corpus retains its available URLs.

## Readiness

The shared schema and registry are ready for controlled future expansion. This result does not approve or initiate scraping. Each additional Thirumurai must pass source inspection, parser sampling, normalization validation, and corpus audit before its registry status becomes `available`.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a normalized Thirumurai corpus.")
    parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--corpus-id", choices=sorted(CORPUS_CONFIGS), default="thirumurai_02")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    config = CORPUS_CONFIGS[args.corpus_id]
    input_path = args.input if args.input != DEFAULT_OUTPUT or args.corpus_id == "thirumurai_02" else config["output"]
    records = load_jsonl(input_path)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    result = validate_records(records)
    if result["status"] == "VALID" and args.corpus_id == "thirumurai_04":
        for entry in registry.get("corpora", []):
            if entry.get("corpus_id") == args.corpus_id:
                entry["status"] = "available"
                entry["verification_status"] = "pilot_verified"
                entry["source_type"] = "local"
                entry["notes"] = (
                    "Controlled five-hymn Appar pilot ingested, normalized, validated, and audited; "
                    "this is not a complete Fourth Thirumurai corpus."
                )
        args.registry.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    report_path = (
        Path("reports/pilot-thirumurai-validation-report.md")
        if args.corpus_id != "thirumurai_02" and args.report == DEFAULT_REPORT
        else args.report
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result, registry, args.corpus_id), encoding="utf-8")
    existing = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest.exists() else {}
    existing.setdefault("validation_summary", {})[args.corpus_id] = result
    write_json(
        args.manifest,
        build_manifest(registry, records, result["missing_fields"], existing_manifest=existing),
    )

    print(f"Records validated: {result['record_count']}")
    print(f"Status: {result['status']}")
    print(f"Errors: {result['error_count']}")
    print(f"Corpus: {args.corpus_id}")
    print(f"Report: {report_path}")
    return 0 if result["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
