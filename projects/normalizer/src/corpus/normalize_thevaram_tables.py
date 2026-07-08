from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "thevaram-relational-v1"
NORMALIZATION_VERSION = "thevaram-normalized-v1"
DEFAULT_INPUT_ROOT = Path("data/processed/thevaram")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_REPORT = Path("reports/thevaram-normalization-report.md")

TABLE_ORDER = (
    "thirumurai_books",
    "paadal_thogupugal",
    "paadalgal",
    "commentaries",
    "text_spans",
)

INLINE_TEXT_FIELDS = {
    "thirumurai_books": (
        "corpus_id",
        "title",
        "work_id",
        "work_title",
        "author",
        "nayanmar",
        "source_url",
    ),
    "paadal_thogupugal": (
        "thogupu_id",
        "title",
        "paadapatta_thalam",
        "title_note",
        "pann",
        "source_url",
        "source_subid",
    ),
    "paadalgal": (
        "paadal_id",
        "thogupu_id",
        "global_song_no",
        "source_song_no",
        "local_song_no",
        "source_url",
        "commentary_url",
    ),
    "commentaries": (
        "commentary_id",
        "paadal_id",
        "extraction_status",
    ),
}

MULTILINE_TEXT_FIELDS = {
    "paadalgal": ("paadal_text",),
    "commentaries": ("kurippurai", "pozhppurai"),
}

TOKEN_SPLIT_RE = re.compile(r"[\s,.;:!?()\[\]{}\"'“”‘’\-]+")
ZERO_WIDTH_CHARS = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\ufeff",
}
LEGACY_CONTROL_CHARS = {
    "\x97": "-",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def canonicalize_chars(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text or "")
    for bad, replacement in LEGACY_CONTROL_CHARS.items():
        normalized = normalized.replace(bad, replacement)
    for char in ZERO_WIDTH_CHARS:
        normalized = normalized.replace(char, "")
    return normalized.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")


def normalize_inline_text(text: str) -> str:
    return " ".join(canonicalize_chars(text).split())


def normalize_multiline_text(text: str) -> str:
    value = canonicalize_chars(text)
    lines = [" ".join(line.split()) for line in value.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def tokenize_tamil_text(text: str) -> list[str]:
    return [token for token in TOKEN_SPLIT_RE.split(text) if token]


def line_spans(parent_id: str, field_name: str, span_type: str, text: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    cursor = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        start = text.find(line, cursor)
        if start < 0:
            continue
        end = start + len(line)
        cursor = end
        if line.strip():
            spans.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "normalization_version": NORMALIZATION_VERSION,
                    "span_id": f"{parent_id}_{field_name}_{line_no}",
                    "parent_id": parent_id,
                    "field_name": field_name,
                    "span_type": span_type,
                    "start_char": start,
                    "end_char": end,
                    "text": line,
                    "metadata": {"line_no": str(line_no)},
                }
            )
    return spans


def normalize_source_parameters(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        normalize_inline_text(str(key)): normalize_inline_text(str(item))
        for key, item in value.items()
    }


def normalize_warnings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [normalize_inline_text(str(item)) for item in value if normalize_inline_text(str(item))]


def normalize_metadata(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        normalize_inline_text(str(key)): normalize_inline_text(str(item))
        for key, item in value.items()
    }


def normalize_table_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["schema_version"] = SCHEMA_VERSION
    normalized["normalization_version"] = NORMALIZATION_VERSION

    for field in INLINE_TEXT_FIELDS.get(table, ()):
        if field in normalized:
            normalized[field] = normalize_inline_text(str(normalized[field]))
    for field in MULTILINE_TEXT_FIELDS.get(table, ()):
        if field in normalized:
            normalized[field] = normalize_multiline_text(str(normalized[field]))

    if table == "paadalgal":
        normalized["source_parameters"] = normalize_source_parameters(
            normalized.get("source_parameters", {})
        )
        normalized["tokenized_paadal"] = tokenize_tamil_text(
            str(normalized.get("paadal_text", ""))
        )
    if table == "commentaries":
        normalized["warnings"] = normalize_warnings(normalized.get("warnings", []))
    if table == "text_spans":
        normalized["span_id"] = normalize_inline_text(str(normalized.get("span_id", "")))
        normalized["parent_id"] = normalize_inline_text(str(normalized.get("parent_id", "")))
        normalized["field_name"] = normalize_inline_text(str(normalized.get("field_name", "")))
        normalized["span_type"] = normalize_inline_text(str(normalized.get("span_type", "")))
        normalized["text"] = normalize_multiline_text(str(normalized.get("text", "")))
        normalized["metadata"] = normalize_metadata(normalized.get("metadata", {}))
    return normalized


def rebuild_text_spans(
    paadalgal: list[dict[str, Any]], commentaries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for paadal in paadalgal:
        spans.extend(
            line_spans(
                str(paadal["paadal_id"]),
                "paadal_text",
                "paadal_line",
                str(paadal.get("paadal_text", "")),
            )
        )
    for commentary in commentaries:
        parent_id = str(commentary["paadal_id"])
        for field_name, span_type in (
            ("kurippurai", "commentary_kurippurai"),
            ("pozhppurai", "commentary_pozhppurai"),
        ):
            text = str(commentary.get(field_name, ""))
            if text:
                spans.extend(line_spans(parent_id, field_name, span_type, text))
    return spans


def newline_count(rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> int:
    count = 0
    field_set = set(fields)
    for row in rows:
        for field in field_set:
            value = row.get(field)
            if isinstance(value, str):
                count += value.count("\n")
    return count


def changed_field_counts(
    original: dict[str, list[dict[str, Any]]],
    normalized: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, int]]:
    changes: dict[str, dict[str, int]] = {}
    for table, rows in original.items():
        if table == "text_spans":
            changes[table] = {
                "rebuilt_from_normalized_text": len(normalized.get(table, []))
            }
            continue
        table_changes: Counter[str] = Counter()
        for before, after in zip(rows, normalized.get(table, []), strict=False):
            for field, before_value in before.items():
                if after.get(field) != before_value:
                    table_changes[field] += 1
        changes[table] = dict(sorted(table_changes.items()))
    return changes


def normalize_tables(input_root: Path, output_root: Path) -> dict[str, Any]:
    source = {table: read_jsonl(input_root / f"{table}.jsonl") for table in TABLE_ORDER}
    normalized: dict[str, list[dict[str, Any]]] = {}
    for table in TABLE_ORDER:
        if table == "text_spans":
            continue
        normalized[table] = [normalize_table_row(table, row) for row in source[table]]
    normalized["text_spans"] = rebuild_text_spans(
        normalized["paadalgal"], normalized["commentaries"]
    )

    counts = {
        table: write_jsonl(output_root / f"{table}.jsonl", normalized[table])
        for table in TABLE_ORDER
    }
    original_newlines = {
        "paadal_text": newline_count(source["paadalgal"], ["paadal_text"]),
        "commentary_text": newline_count(source["commentaries"], ["kurippurai", "pozhppurai"]),
    }
    normalized_newlines = {
        "paadal_text": newline_count(normalized["paadalgal"], ["paadal_text"]),
        "commentary_text": newline_count(normalized["commentaries"], ["kurippurai", "pozhppurai"]),
    }
    report = {
        "normalization_version": NORMALIZATION_VERSION,
        "input_root": str(input_root),
        "output_root": str(output_root),
        "counts": counts,
        "changed_fields": changed_field_counts(source, normalized),
        "newline_counts_before": original_newlines,
        "newline_counts_after": normalized_newlines,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "normalization_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def render_report(report: dict[str, Any]) -> str:
    count_rows = "\n".join(
        f"| `{table}` | {count} |" for table, count in report["counts"].items()
    )
    newline_rows = "\n".join(
        f"| `{field}` | {report['newline_counts_before'][field]} | {report['newline_counts_after'][field]} |"
        for field in report["newline_counts_before"]
    )
    changed_lines: list[str] = []
    for table, fields in report["changed_fields"].items():
        if not fields:
            changed_lines.append(f"- `{table}`: none")
            continue
        field_text = ", ".join(f"`{field}`={count}" for field, count in fields.items())
        changed_lines.append(f"- `{table}`: {field_text}")
    return f"""# Thevaram Normalization Report

## Summary

- Normalization version: `{report["normalization_version"]}`
- Input root: `{report["input_root"]}`
- Output root: `{report["output_root"]}`
- Raw and parsed source tables were not modified.

## Counts

| Table | Rows |
| --- | ---: |
{count_rows}

## Preserved Line Structure

Existing `\\n` line boundaries are intentionally preserved because they identify poem and commentary line breaks. Normalization only canonicalizes Unicode, removes unsafe invisible/control characters, collapses repeated spaces inside each line, trims line edges, and recomputes span offsets against the normalized text.

| Field group | Before `\\n` count | After `\\n` count |
| --- | ---: | ---: |
{newline_rows}

## Changed Fields

{chr(10).join(changed_lines)}
"""


def write_report(report: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize Thevaram 1-8 relational tables.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    report = normalize_tables(args.input_root, args.output_root)
    write_report(report, args.report)
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "newline_counts_before": report["newline_counts_before"],
                "newline_counts_after": report["newline_counts_after"],
                "output_root": report["output_root"],
                "report": str(args.report),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
