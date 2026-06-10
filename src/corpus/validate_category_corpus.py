from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.pilot_ingest_category import DEFAULT_PLAN, load_json, load_jsonl

REQUIRED_FIELDS = {
    "schema_version": str,
    "record_id": str,
    "record_type": str,
    "category_id": str,
    "book_id": str,
    "work_id": str,
    "language": str,
    "content_text": str,
    "source_url": str,
    "source_metadata": dict,
    "parser_family": str,
}


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_records(records: list[dict[str, Any]], category_id: str) -> dict[str, Any]:
    missing: Counter[str] = Counter()
    invalid_types: Counter[str] = Counter()
    malformed_urls = 0
    category_mismatches = 0
    ids: Counter[str] = Counter()

    for record in records:
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in record:
                missing[field] += 1
            elif not isinstance(record[field], expected_type):
                invalid_types[field] += 1
            elif isinstance(record[field], str) and not record[field].strip():
                missing[field] += 1
        if not str(record.get("content_text") or record.get("verse_text") or "").strip():
            missing["content_text_or_verse_text"] += 1
        if record.get("category_id") != category_id:
            category_mismatches += 1
        if isinstance(record.get("source_url"), str) and not valid_url(record["source_url"]):
            malformed_urls += 1
        record_id = str(record.get("record_id") or "")
        if record_id:
            ids[record_id] += 1

    duplicates = sorted(record_id for record_id, count in ids.items() if count > 1)
    error_count = (
        sum(missing.values())
        + sum(invalid_types.values())
        + malformed_urls
        + category_mismatches
        + len(duplicates)
    )
    return {
        "category_id": category_id,
        "record_count": len(records),
        "status": "VALID" if records and error_count == 0 else "INVALID",
        "error_count": error_count if records else error_count + 1,
        "missing_fields": dict(sorted(missing.items())),
        "invalid_field_types": dict(sorted(invalid_types.items())),
        "malformed_source_urls": malformed_urls,
        "category_mismatches": category_mismatches,
        "duplicate_record_ids": duplicates,
        "source_url_coverage": (
            sum(bool(record.get("source_url")) for record in records) / len(records)
            if records
            else 0.0
        ),
    }


def render_validation_report(result: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"| `{field}` | {count} |"
        for field, count in result["missing_fields"].items()
    ) or "| None | 0 |"
    return f"""# Multi-Category Pilot Validation Report

## Verified Sample

- Category: `{result['category_id']}`
- Records: `{result['record_count']}`
- Status: `{result['status']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Duplicate record IDs: `{len(result['duplicate_record_ids'])}`
- Malformed source URLs: `{result['malformed_source_urls']}`
- Category mismatches: `{result['category_mismatches']}`

## Missing Fields

| Field | Count |
| --- | ---: |
{missing_rows}

## Safety Result

The verified sample used an existing local, validated corpus artifact. Network requests,
website discovery, full-category scraping, LLM calls, and mutation of frozen corpora were
all outside this run.
"""


def render_comparison_report(
    plan: dict[str, Any], verified: dict[str, Any] | None = None
) -> str:
    rows = []
    for pilot in plan.get("pilots", []):
        is_verified = verified and pilot["category_id"] == verified["category_id"]
        rows.append(
            "| {category} | `{family}` | {records} | {missing} | {coverage} | {content} | {risk} | {suitability} |".format(
                category=pilot["category_tamil"],
                family=pilot["parser_family"],
                records=verified["record_count"] if is_verified else 0,
                missing=sum(verified["missing_fields"].values()) if is_verified else "Not tested",
                coverage=f"{verified['source_url_coverage']:.1%}" if is_verified else "Not tested",
                content="Validated verse/commentary seed" if is_verified else "Pending inspected sample",
                risk="Existing source family only" if is_verified else "HTML hierarchy unknown",
                suitability="Framework verified" if is_verified else "Source inspection required",
            )
        )
    return """# Multi-Category Pilot Comparison Report

This table compares only bounded pilot readiness. A planned row does not imply that source
content has been fetched or approved.

| Category | Parser Family | Records | Missing Fields | URL Coverage | Content Type | Extraction Risks | Next Expansion |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
{rows}

## Finding

The shared contract works for the existing Saivam verse/commentary seed. Grammar, Sangam,
prose, dictionary, and encyclopedia pilots still require source inspection and local
fixtures before ingestion. This is the principal risk and the intended control point.
""".format(rows="\n".join(rows))


def validate_category(
    category_id: str,
    *,
    base_dir: Path = Path("."),
    input_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    source = input_path or (
        base_dir
        / "data/processed/normalized_categories"
        / f"{category_id}_normalized.jsonl"
    )
    records = load_jsonl(source, 10)
    result = validate_records(records, category_id)
    report = report_path or base_dir / "reports/multi-category-pilot-validation-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_validation_report(result), encoding="utf-8")
    plan = load_json(base_dir / DEFAULT_PLAN)
    comparison = base_dir / "reports/multi-category-pilot-comparison-report.md"
    comparison.write_text(render_comparison_report(plan, result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one normalized category pilot.")
    parser.add_argument("--category-id", required=True)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_category(
            args.category_id,
            base_dir=args.base_dir,
            input_path=args.input,
            report_path=args.report,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
