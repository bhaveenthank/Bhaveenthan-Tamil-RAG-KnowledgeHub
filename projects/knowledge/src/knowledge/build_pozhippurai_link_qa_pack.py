from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_LINKS = Path("data/processed/thevaram_pozhippurai_links_v2/paadal_pozhippurai_links.jsonl")
DEFAULT_OUTPUT_DIR = Path("data/processed/thevaram_pozhippurai_links_v2/qa_review_pack")
DEFAULT_REPORT = Path("reports/thevaram-pozhppurai-link-v2-qa-review-pack.md")

DECISION_VALUES = [
    "ACCEPT",
    "WRONG_TARGET",
    "PARTIAL_MATCH",
    "WRONG_RELATION_TYPE",
    "NEEDS_SPLIT",
    "NO_LINK_POSSIBLE",
]

CONFIDENCE_QUOTAS = {
    "high": 30,
    "medium": 50,
    "low": 90,
    "none": 20,
}

RELATIONSHIP_QUOTA = 8
THIRUMURAI_QUOTA = 5
DIAGNOSTIC_QUOTA = 10
TARGET_SAMPLE_COUNT = 210


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("thirumurai_no", "")),
        str(row.get("paadal_id", "")),
        int(row.get("source_line_no") or 0),
        str(row.get("link_id", "")),
    )


def spread_sample(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count <= 0 or not rows:
        return []
    rows = sorted(rows, key=sort_key)
    if len(rows) <= count:
        return rows
    if count == 1:
        return [rows[len(rows) // 2]]
    indexes = [round(index * (len(rows) - 1) / (count - 1)) for index in range(count)]
    selected: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for index in indexes:
        if index not in seen_indexes:
            selected.append(rows[index])
            seen_indexes.add(index)
    cursor = 0
    while len(selected) < count and cursor < len(rows):
        if cursor not in seen_indexes:
            selected.append(rows[cursor])
            seen_indexes.add(cursor)
        cursor += 1
    return selected[:count]


def add_rows(
    selected: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
    *,
    count: int,
    reason: str,
) -> None:
    for row in spread_sample(rows, count):
        link_id = str(row["link_id"])
        if link_id not in selected:
            item = dict(row)
            item["_sample_reason"] = reason
            selected[link_id] = item


def build_samples(links: list[dict[str, Any]], target_count: int = TARGET_SAMPLE_COUNT) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}

    relationships = sorted(
        relation for relation in {str(row.get("relationship_type", "")) for row in links}
        if relation and relation != "unlinked"
    )
    for thirumurai_no in sorted({str(row.get("thirumurai_no", "")) for row in links}):
        add_rows(
            selected,
            [row for row in links if str(row.get("thirumurai_no", "")) == thirumurai_no],
            count=THIRUMURAI_QUOTA,
            reason=f"thirumurai_{thirumurai_no}",
        )

    for relationship in relationships:
        add_rows(
            selected,
            [row for row in links if row.get("relationship_type") == relationship],
            count=RELATIONSHIP_QUOTA,
            reason=f"relationship_{relationship}",
        )

    for diagnostic in sorted({str(row.get("diagnostic_category", "")) for row in links if row.get("diagnostic_category")}):
        add_rows(
            selected,
            [row for row in links if row.get("diagnostic_category") == diagnostic],
            count=DIAGNOSTIC_QUOTA,
            reason=f"diagnostic_{diagnostic}",
        )

    for confidence, quota in CONFIDENCE_QUOTAS.items():
        add_rows(
            selected,
            [row for row in links if row.get("confidence") == confidence],
            count=quota,
            reason=f"confidence_{confidence}",
        )

    edge_cases = [
        row
        for row in links
        if row.get("confidence") == "low"
        and float(row.get("score") or 0.0) >= 0.24
        and row.get("link_status") == "linked_low_confidence"
    ]
    add_rows(selected, edge_cases, count=20, reason="near_threshold_low_confidence")

    if len(selected) < target_count:
        add_rows(
            selected,
            [row for row in links if row.get("confidence") != "none"],
            count=target_count - len(selected),
            reason="top_up_non_empty_links",
        )
    if len(selected) < target_count:
        add_rows(
            selected,
            links,
            count=target_count - len(selected),
            reason="top_up_any_status",
        )

    return list(selected.values())[:target_count]


def review_row(sample_no: int, row: dict[str, Any]) -> dict[str, Any]:
    features = row.get("features") or {}
    return {
        "qa_id": f"PPL_QA_{sample_no:03d}",
        "sample_reason": row.get("_sample_reason", ""),
        "link_id": row.get("link_id", ""),
        "paadal_id": row.get("paadal_id", ""),
        "commentary_id": row.get("commentary_id", ""),
        "thirumurai_no": row.get("thirumurai_no", ""),
        "source_line_no": row.get("source_line_no", ""),
        "relationship_type_v1": row.get("relationship_type", ""),
        "confidence_v1": row.get("confidence", ""),
        "score_v1": row.get("score", ""),
        "link_status_v1": row.get("link_status", ""),
        "diagnostic_category": row.get("diagnostic_category", ""),
        "problem_reason": row.get("problem_reason", ""),
        "source_text": row.get("source_text", ""),
        "target_text": row.get("target_text", ""),
        "source_offsets": f"{row.get('source_start_char')}:{row.get('source_end_char')}",
        "target_offsets": (
            ""
            if row.get("target_start_char") is None
            else f"{row.get('target_start_char')}:{row.get('target_end_char')}"
        ),
        "token_score": features.get("token_score", ""),
        "char_score": features.get("char_score", ""),
        "entity_score": features.get("entity_score", ""),
        "containment_score": features.get("containment_score", ""),
        "order_score": features.get("order_score", ""),
        "score_margin": features.get("score_margin", ""),
        "window_size": features.get("window_size", ""),
        "review_question": "Does the target pozhppurai span correctly explain this paadal line?",
        "allowed_decisions": "|".join(DECISION_VALUES),
        "manual_decision": "",
        "correct_relationship_type": "",
        "correct_target_text_or_note": "",
        "v2_rule_suggestion": "",
        "reviewer_notes": "",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_report(samples: list[dict[str, Any]], output_csv: Path) -> str:
    confidence_counts = Counter(row["confidence_v1"] for row in samples)
    relationship_counts = Counter(row["relationship_type_v1"] for row in samples)
    thirumurai_counts = Counter(str(row["thirumurai_no"]) for row in samples)
    diagnostic_counts = Counter(str(row.get("diagnostic_category", "")) for row in samples)
    reason_counts = Counter(row["sample_reason"] for row in samples)

    def table(counter: Counter[str]) -> str:
        return "\n".join(f"| `{key}` | {counter[key]} |" for key in sorted(counter)) or "| None | 0 |"

    return f"""# Thevaram Pozhippurai Link QA Review Pack

## Purpose

This pack gives a balanced sample of paadal-line to pozhppurai-segment links for manual
review. It is meant to produce a decision table for the next linker version, not to
review all generated links one by one.

## Files

- Review CSV: `{output_csv}`

## How To Review

Fill `manual_decision` with one of:

- `ACCEPT`: target span correctly explains the paadal line.
- `WRONG_TARGET`: target span is the wrong pozhppurai segment.
- `PARTIAL_MATCH`: target is related but incomplete or too broad.
- `WRONG_RELATION_TYPE`: target is right, but relationship type is wrong.
- `NEEDS_SPLIT`: one line should map to multiple pozhppurai spans.
- `NO_LINK_POSSIBLE`: no useful pozhppurai span exists for this line.

Use `correct_relationship_type`, `correct_target_text_or_note`, and `v2_rule_suggestion`
only when you want the next linker to learn a correction.

## Sample Size

- Rows: `{len(samples)}`

## Confidence Coverage

| Confidence | Samples |
| --- | ---: |
{table(confidence_counts)}

## Relationship Coverage

| Relationship | Samples |
| --- | ---: |
{table(relationship_counts)}

## Thirumurai Coverage

| Thirumurai | Samples |
| --- | ---: |
{table(thirumurai_counts)}

## Diagnostic Category Coverage

| Category | Samples |
| --- | ---: |
{table(diagnostic_counts)}

## Sampling Reasons

| Reason | Samples |
| --- | ---: |
{table(reason_counts)}
"""


def build_review_pack(
    *,
    links_path: Path = DEFAULT_LINKS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report_path: Path = DEFAULT_REPORT,
    target_count: int = TARGET_SAMPLE_COUNT,
) -> dict[str, Any]:
    links = read_jsonl(links_path)
    samples = [review_row(index, row) for index, row in enumerate(build_samples(links, target_count), start=1)]
    output_csv = output_dir / "paadal_pozhippurai_link_qa_samples.csv"
    write_csv(output_csv, samples)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "sample_count": len(samples),
        "links_path": str(links_path),
        "output_csv": str(output_csv),
        "report": str(report_path),
        "confidence_counts": dict(sorted(Counter(row["confidence_v1"] for row in samples).items())),
        "relationship_counts": dict(sorted(Counter(row["relationship_type_v1"] for row in samples).items())),
        "thirumurai_counts": dict(sorted(Counter(str(row["thirumurai_no"]) for row in samples).items())),
        "diagnostic_counts": dict(sorted(Counter(str(row.get("diagnostic_category", "")) for row in samples).items())),
        "sample_reason_counts": dict(sorted(Counter(row["sample_reason"] for row in samples).items())),
    }
    (output_dir / "qa_pack_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(samples, output_csv), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a manual QA review pack for Thevaram paadal-pozhppurai links.")
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--target-count", type=int, default=TARGET_SAMPLE_COUNT)
    args = parser.parse_args(argv)
    summary = build_review_pack(
        links_path=args.links,
        output_dir=args.output_dir,
        report_path=args.report,
        target_count=args.target_count,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
