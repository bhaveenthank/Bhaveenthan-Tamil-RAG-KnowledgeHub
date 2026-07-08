from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "thevaram-relational-v1"
DEFAULT_TABLE_ROOT = Path("data/processed/thevaram")
DEFAULT_REPORT = Path("reports/thevaram-table-quality-report.md")

TABLE_KEYS: dict[str, str] = {
    "thirumurai_books": "corpus_id",
    "paadal_thogupugal": "thogupu_id",
    "paadalgal": "paadal_id",
    "commentaries": "commentary_id",
    "text_spans": "span_id",
}

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "thirumurai_books": {
        "schema_version",
        "thirumurai_no",
        "corpus_id",
        "title",
        "work_id",
        "work_title",
        "author",
        "source_url",
    },
    "paadal_thogupugal": {
        "schema_version",
        "thogupu_id",
        "thirumurai_no",
        "ordinal",
        "title",
        "paadapatta_thalam",
        "pann",
        "source_url",
        "source_subid",
    },
    "paadalgal": {
        "schema_version",
        "paadal_id",
        "thogupu_id",
        "thirumurai_no",
        "global_song_no",
        "source_song_no",
        "local_song_no",
        "verse_index_in_thogupu",
        "paadal_text",
        "tokenized_paadal",
        "source_url",
        "commentary_url",
        "source_parameters",
    },
    "commentaries": {
        "schema_version",
        "commentary_id",
        "paadal_id",
        "kurippurai",
        "pozhppurai",
        "extraction_status",
        "warnings",
    },
    "text_spans": {
        "schema_version",
        "span_id",
        "parent_id",
        "field_name",
        "span_type",
        "start_char",
        "end_char",
        "text",
        "metadata",
    },
}

HTML_ARTIFACT_RE = re.compile(r"<[a-zA-Z!/][^>]*>|&(?:nbsp|amp|lt|gt|quot);|�")
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")


@dataclass(frozen=True, slots=True)
class QualityIssue:
    severity: str
    code: str
    table: str
    row_id: str
    message: str


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_line_no"] = line_no
                rows.append(row)
    return rows


def load_tables(root: Path) -> tuple[dict[str, list[dict[str, object]]], list[QualityIssue]]:
    tables: dict[str, list[dict[str, object]]] = {}
    issues: list[QualityIssue] = []
    for table in TABLE_KEYS:
        path = root / f"{table}.jsonl"
        if not path.exists():
            issues.append(QualityIssue("critical", "missing_table", table, "", f"Missing {path}"))
            tables[table] = []
            continue
        try:
            tables[table] = read_jsonl(path)
        except Exception as exc:
            issues.append(QualityIssue("critical", "invalid_jsonl", table, "", str(exc)))
            tables[table] = []
    return tables, issues


def tamil_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    tamil = sum(1 for char in letters if TAMIL_RE.match(char))
    return tamil / len(letters)


def numeric(value: object) -> int | None:
    text = str(value).strip()
    if not text.isdigit():
        return None
    return int(text)


def row_id(table: str, row: dict[str, object]) -> str:
    return str(row.get(TABLE_KEYS[table], row.get("paadal_id", row.get("parent_id", ""))))


def add_issue(
    issues: list[QualityIssue],
    severity: str,
    code: str,
    table: str,
    row: dict[str, object] | str,
    message: str,
) -> None:
    rid = row if isinstance(row, str) else row_id(table, row)
    issues.append(QualityIssue(severity, code, table, rid, message))


def check_required_columns(tables: dict[str, list[dict[str, object]]], issues: list[QualityIssue]) -> None:
    for table, rows in tables.items():
        required = REQUIRED_COLUMNS[table]
        key = TABLE_KEYS[table]
        seen: Counter[str] = Counter()
        for row in rows:
            rid = str(row.get(key, ""))
            missing = sorted(required - row.keys())
            if missing:
                add_issue(issues, "critical", "missing_columns", table, rid, f"Missing columns: {missing}")
            if row.get("schema_version") != SCHEMA_VERSION:
                add_issue(
                    issues,
                    "critical",
                    "schema_version_mismatch",
                    table,
                    rid,
                    f"Expected {SCHEMA_VERSION}, got {row.get('schema_version')!r}",
                )
            if not rid:
                add_issue(issues, "critical", "empty_primary_key", table, rid, f"Empty {key}")
            else:
                seen[rid] += 1
        for duplicate_id, count in seen.items():
            if count > 1:
                issues.append(
                    QualityIssue(
                        "critical",
                        "duplicate_primary_key",
                        table,
                        duplicate_id,
                        f"{duplicate_id} appears {count} times",
                    )
                )


def check_foreign_keys(tables: dict[str, list[dict[str, object]]], issues: list[QualityIssue]) -> None:
    book_numbers = {row.get("thirumurai_no") for row in tables["thirumurai_books"]}
    thogupu_ids = {row.get("thogupu_id") for row in tables["paadal_thogupugal"]}
    paadal_ids = {row.get("paadal_id") for row in tables["paadalgal"]}
    text_parent_ids = paadal_ids | {row.get("commentary_id") for row in tables["commentaries"]}

    for row in tables["paadal_thogupugal"]:
        if row.get("thirumurai_no") not in book_numbers:
            add_issue(issues, "critical", "missing_book_fk", "paadal_thogupugal", row, "Unknown thirumurai_no")
    for row in tables["paadalgal"]:
        if row.get("thogupu_id") not in thogupu_ids:
            add_issue(issues, "critical", "missing_thogupu_fk", "paadalgal", row, "Unknown thogupu_id")
    for row in tables["commentaries"]:
        if row.get("paadal_id") not in paadal_ids:
            add_issue(issues, "critical", "missing_paadal_fk", "commentaries", row, "Unknown paadal_id")
    commentary_by_paadal = Counter(str(row.get("paadal_id")) for row in tables["commentaries"])
    for paadal_id in paadal_ids:
        count = commentary_by_paadal[str(paadal_id)]
        if count == 0:
            issues.append(QualityIssue("critical", "missing_commentary_row", "commentaries", str(paadal_id), "No commentary row"))
        elif count > 1:
            issues.append(QualityIssue("critical", "duplicate_commentary_row", "commentaries", str(paadal_id), f"{count} commentary rows"))
    for row in tables["text_spans"]:
        if row.get("parent_id") not in text_parent_ids:
            add_issue(issues, "critical", "missing_span_parent_fk", "text_spans", row, "Unknown parent_id")


def check_text_quality(tables: dict[str, list[dict[str, object]]], issues: list[QualityIssue]) -> None:
    for row in tables["paadalgal"]:
        text = str(row.get("paadal_text", ""))
        if not text.strip():
            add_issue(issues, "critical", "empty_paadal_text", "paadalgal", row, "Empty paadal_text")
        if unicodedata.normalize("NFC", text) != text:
            add_issue(issues, "major", "non_nfc_text", "paadalgal", row, "paadal_text is not NFC normalized")
        if HTML_ARTIFACT_RE.search(text):
            add_issue(issues, "major", "html_artifact_in_text", "paadalgal", row, "HTML/entity artifact in paadal_text")
        if tamil_ratio(text) < 0.75:
            add_issue(issues, "major", "low_tamil_ratio", "paadalgal", row, "paadal_text has low Tamil letter ratio")
        tokens = row.get("tokenized_paadal", [])
        if not isinstance(tokens, list) or not tokens:
            add_issue(issues, "major", "empty_tokenized_paadal", "paadalgal", row, "Missing tokenized_paadal")
        if str(row.get("global_song_no", "")).strip() not in str(row.get("paadal_id", "")):
            add_issue(issues, "minor", "song_no_not_in_id", "paadalgal", row, "global_song_no not visible in paadal_id")

    for row in tables["commentaries"]:
        status = str(row.get("extraction_status", ""))
        kurippurai = str(row.get("kurippurai", ""))
        pozhppurai = str(row.get("pozhppurai", ""))
        combined = f"{kurippurai}\n{pozhppurai}"
        stripped_combined = combined.strip()
        if status == "success" and not combined.strip():
            add_issue(issues, "major", "empty_success_commentary", "commentaries", row, "Successful commentary has no text")
        if status == "commentary_fetch_failed" and stripped_combined:
            add_issue(issues, "minor", "failed_commentary_has_text", "commentaries", row, "Non-success commentary has text")
        if stripped_combined and unicodedata.normalize("NFC", combined) != combined:
            add_issue(issues, "major", "non_nfc_commentary", "commentaries", row, "Commentary text is not NFC normalized")
        if stripped_combined and HTML_ARTIFACT_RE.search(combined):
            add_issue(issues, "major", "html_artifact_in_commentary", "commentaries", row, "HTML/entity artifact in commentary")
        if stripped_combined and tamil_ratio(combined) < 0.75:
            add_issue(issues, "major", "low_tamil_ratio_commentary", "commentaries", row, "Commentary has low Tamil letter ratio")


def check_metadata_quality(tables: dict[str, list[dict[str, object]]], issues: list[QualityIssue]) -> None:
    for row in tables["paadal_thogupugal"]:
        for field in ("title", "paadapatta_thalam", "source_url", "source_subid"):
            if not str(row.get(field, "")).strip():
                add_issue(issues, "major", f"empty_{field}", "paadal_thogupugal", row, f"Empty {field}")
        if not str(row.get("source_url", "")).startswith("https://www.tamilvu.org/"):
            add_issue(issues, "major", "unexpected_source_url", "paadal_thogupugal", row, "Source URL is not TamilVU HTTPS")
        if str(row.get("source_subid", "")) not in str(row.get("source_url", "")):
            add_issue(issues, "major", "source_subid_url_mismatch", "paadal_thogupugal", row, "source_subid missing from source_url")

    thogupu_by_id = {row["thogupu_id"]: row for row in tables["paadal_thogupugal"] if "thogupu_id" in row}
    for row in tables["paadalgal"]:
        if not str(row.get("source_url", "")).startswith("https://www.tamilvu.org/"):
            add_issue(issues, "major", "unexpected_source_url", "paadalgal", row, "Source URL is not TamilVU HTTPS")
        if str(row.get("commentary_url", "")) and not str(row.get("commentary_url", "")).startswith("https://www.tamilvu.org/"):
            add_issue(issues, "major", "unexpected_commentary_url", "paadalgal", row, "Commentary URL is not TamilVU HTTPS")
        params = row.get("source_parameters", {})
        if isinstance(params, dict):
            source_song_no = str(row.get("source_song_no") or row.get("global_song_no", ""))
            if str(params.get("song_no", "")) != source_song_no:
                add_issue(issues, "major", "song_no_param_mismatch", "paadalgal", row, "source_parameters.song_no mismatch")
            thogupu = thogupu_by_id.get(row.get("thogupu_id"))
            if thogupu and str(params.get("sub_id", "")) != str(thogupu.get("source_subid", "")):
                add_issue(issues, "major", "sub_id_param_mismatch", "paadalgal", row, "source_parameters.sub_id mismatch")
        else:
            add_issue(issues, "major", "invalid_source_parameters", "paadalgal", row, "source_parameters is not an object")


def check_numbering(tables: dict[str, list[dict[str, object]]], issues: list[QualityIssue]) -> None:
    thogupugal_by_thirumurai: dict[int, list[dict[str, object]]] = defaultdict(list)
    paadalgal_by_thogupu: dict[str, list[dict[str, object]]] = defaultdict(list)
    paadalgal_by_thirumurai: dict[int, list[dict[str, object]]] = defaultdict(list)

    for row in tables["paadal_thogupugal"]:
        no = numeric(row.get("thirumurai_no"))
        if no is not None:
            thogupugal_by_thirumurai[no].append(row)
    for row in tables["paadalgal"]:
        paadalgal_by_thogupu[str(row.get("thogupu_id"))].append(row)
        no = numeric(row.get("thirumurai_no"))
        if no is not None:
            paadalgal_by_thirumurai[no].append(row)

    for thirumurai_no, rows in thogupugal_by_thirumurai.items():
        ordinals = sorted(numeric(row.get("ordinal")) for row in rows)
        ordinals = [item for item in ordinals if item is not None]
        expected = list(range(1, len(ordinals) + 1))
        if ordinals != expected:
            issues.append(
                QualityIssue(
                    "major",
                    "non_contiguous_thogupu_ordinals",
                    "paadal_thogupugal",
                    f"thirumurai_{thirumurai_no:02d}",
                    f"Expected ordinals 1..{len(ordinals)}, got gaps/duplicates",
                )
            )

    for thogupu_id, rows in paadalgal_by_thogupu.items():
        indexes = sorted(numeric(row.get("verse_index_in_thogupu")) for row in rows)
        indexes = [item for item in indexes if item is not None]
        expected = list(range(1, len(indexes) + 1))
        if indexes != expected:
            issues.append(
                QualityIssue(
                    "major",
                    "non_contiguous_verse_indexes",
                    "paadalgal",
                    thogupu_id,
                    f"Expected verse_index_in_thogupu 1..{len(indexes)}, got gaps/duplicates",
                )
            )

    for thirumurai_no, rows in paadalgal_by_thirumurai.items():
        rows_by_song_no: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            song_no = str(row.get("global_song_no", "")).strip()
            if song_no:
                rows_by_song_no[song_no].append(row)
        numeric_song_numbers = [
            numeric(row.get("global_song_no"))
            for row in rows
            if numeric(row.get("global_song_no")) is not None
        ]
        for song_no, duplicate_rows in rows_by_song_no.items():
            if len(duplicate_rows) > 1:
                examples = ", ".join(str(row.get("paadal_id")) for row in duplicate_rows[:3])
                issues.append(
                    QualityIssue(
                        "major",
                        "duplicate_source_song_number",
                        "paadalgal",
                        f"thirumurai_{thirumurai_no:02d}_song_{song_no}",
                        f"global_song_no {song_no} appears {len(duplicate_rows)} times: {examples}",
                    )
                )
        if numeric_song_numbers != sorted(numeric_song_numbers):
            issues.append(
                QualityIssue(
                    "minor",
                    "non_monotonic_song_order",
                    "paadalgal",
                    f"thirumurai_{thirumurai_no:02d}",
                    "global_song_no is not monotonic in file order",
                )
            )


def check_span_offsets(tables: dict[str, list[dict[str, object]]], issues: list[QualityIssue]) -> None:
    text_by_parent_field: dict[tuple[str, str], str] = {}
    for row in tables["paadalgal"]:
        text_by_parent_field[(str(row.get("paadal_id")), "paadal_text")] = str(row.get("paadal_text", ""))
    for row in tables["commentaries"]:
        parent = str(row.get("paadal_id"))
        text_by_parent_field[(parent, "kurippurai")] = str(row.get("kurippurai", ""))
        text_by_parent_field[(parent, "pozhppurai")] = str(row.get("pozhppurai", ""))

    seen_by_parent_field: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    for row in tables["text_spans"]:
        parent_id = str(row.get("parent_id", ""))
        field_name = str(row.get("field_name", ""))
        text = text_by_parent_field.get((parent_id, field_name))
        if text is None:
            add_issue(issues, "critical", "span_field_missing_parent_text", "text_spans", row, "No text for parent/field")
            continue
        start = numeric(row.get("start_char"))
        end = numeric(row.get("end_char"))
        if start is None or end is None or start < 0 or end < start or end > len(text):
            add_issue(issues, "critical", "invalid_span_bounds", "text_spans", row, f"Invalid bounds {start}:{end}")
            continue
        span_text = str(row.get("text", ""))
        if text[start:end] != span_text:
            add_issue(issues, "critical", "span_text_mismatch", "text_spans", row, "Span text does not match parent text offsets")
        seen_by_parent_field[(parent_id, field_name)].append((start, end, row_id("text_spans", row)))

    for key, spans in seen_by_parent_field.items():
        spans = sorted(spans)
        previous_end = -1
        for start, end, span_id in spans:
            if start < previous_end:
                issues.append(
                    QualityIssue("major", "overlapping_spans", "text_spans", span_id, f"Overlapping span in {key}")
                )
            previous_end = max(previous_end, end)


def audit_tables(root: Path) -> dict[str, object]:
    tables, issues = load_tables(root)
    check_required_columns(tables, issues)
    check_foreign_keys(tables, issues)
    check_metadata_quality(tables, issues)
    check_text_quality(tables, issues)
    check_numbering(tables, issues)
    check_span_offsets(tables, issues)

    severity_order = {"critical": 0, "major": 1, "minor": 2}
    issues = sorted(issues, key=lambda item: (severity_order.get(item.severity, 9), item.code, item.table, item.row_id))
    return {
        "table_root": str(root),
        "counts": {table: len(rows) for table, rows in tables.items()},
        "issue_counts": dict(Counter(issue.severity for issue in issues)),
        "code_counts": dict(sorted(Counter(issue.code for issue in issues).items())),
        "issues": [asdict(issue) for issue in issues],
    }


def render_markdown(report: dict[str, object], max_examples_per_code: int = 10) -> str:
    issues = [QualityIssue(**issue) for issue in report["issues"]]
    grouped: dict[str, list[QualityIssue]] = defaultdict(list)
    for issue in issues:
        grouped[issue.code].append(issue)

    lines = [
        "# Thevaram Table Quality Report",
        "",
        f"- Table root: `{report['table_root']}`",
        "",
        "## Counts",
        "",
    ]
    for table, count in report["counts"].items():
        lines.append(f"- `{table}`: `{count}`")
    lines.extend(["", "## Issue Counts", ""])
    if report["issue_counts"]:
        for severity, count in report["issue_counts"].items():
            lines.append(f"- `{severity}`: `{count}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Issues By Code", ""])
    if not grouped:
        lines.append("- None")
    for code, items in sorted(grouped.items()):
        severity = Counter(issue.severity for issue in items).most_common(1)[0][0]
        lines.append(f"### {code}")
        lines.append("")
        lines.append(f"- Severity: `{severity}`")
        lines.append(f"- Count: `{len(items)}`")
        lines.append("- Examples:")
        for issue in items[:max_examples_per_code]:
            lines.append(
                f"  - `{issue.table}` `{issue.row_id}`: {issue.message}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(report), encoding="utf-8")
    output.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit generated Thevaram relational tables.")
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fail-on", choices=["none", "critical", "major", "minor"], default="none")
    return parser.parse_args(argv)


def should_fail(report: dict[str, object], threshold: str) -> bool:
    if threshold == "none":
        return False
    order = {"critical": 0, "major": 1, "minor": 2}
    max_level = order[threshold]
    return any(order.get(issue["severity"], 9) <= max_level for issue in report["issues"])


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = audit_tables(args.table_root)
    write_report(report, args.report)
    print(json.dumps({k: report[k] for k in ("counts", "issue_counts", "code_counts")}, ensure_ascii=False, indent=2))
    return 1 if should_fail(report, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
