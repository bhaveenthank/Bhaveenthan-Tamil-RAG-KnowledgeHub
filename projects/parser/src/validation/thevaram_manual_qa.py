from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from validation.thevaram_table_quality import DEFAULT_TABLE_ROOT, audit_tables, read_jsonl

DEFAULT_REPORT = Path("reports/thevaram-manual-qa-samples.md")


def compact_text(text: str, limit: int = 260) -> str:
    value = " / ".join(part.strip() for part in text.splitlines() if part.strip())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def pick_positions(rows: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    if not rows or count <= 0:
        return []
    if len(rows) <= count:
        return rows
    positions = sorted({round(index * (len(rows) - 1) / (count - 1)) for index in range(count)})
    return [rows[position] for position in positions]


def load_tables(root: Path) -> dict[str, list[dict[str, object]]]:
    return {
        "thirumurai_books": read_jsonl(root / "thirumurai_books.jsonl"),
        "paadal_thogupugal": read_jsonl(root / "paadal_thogupugal.jsonl"),
        "paadalgal": read_jsonl(root / "paadalgal.jsonl"),
        "commentaries": read_jsonl(root / "commentaries.jsonl"),
        "text_spans": read_jsonl(root / "text_spans.jsonl"),
    }


def sample_paadalgal(paadalgal: list[dict[str, object]], target_count: int) -> list[dict[str, object]]:
    by_thirumurai: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in paadalgal:
        by_thirumurai[int(row["thirumurai_no"])].append(row)
    samples: list[dict[str, object]] = []
    for thirumurai_no in sorted(by_thirumurai):
        samples.extend(pick_positions(by_thirumurai[thirumurai_no], 2))
    if len(samples) < target_count:
        selected_ids = {row["paadal_id"] for row in samples}
        for row in pick_positions(paadalgal, target_count):
            if row["paadal_id"] not in selected_ids:
                samples.append(row)
            if len(samples) >= target_count:
                break
    return samples[:target_count]


def duplicate_source_song_samples(paadalgal: list[dict[str, object]], limit: int = 5) -> list[list[dict[str, object]]]:
    grouped: dict[tuple[int, str], list[dict[str, object]]] = defaultdict(list)
    for row in paadalgal:
        grouped[(int(row["thirumurai_no"]), str(row.get("source_song_no", row["global_song_no"])))].append(row)
    return [rows for _, rows in sorted(grouped.items()) if len(rows) > 1][:limit]


def render_report(root: Path, sample_count: int) -> str:
    tables = load_tables(root)
    audit = audit_tables(root)
    thogupu_by_id = {row["thogupu_id"]: row for row in tables["paadal_thogupugal"]}
    commentary_by_paadal = {row["paadal_id"]: row for row in tables["commentaries"]}
    spans_by_parent: Counter[str] = Counter(str(row["parent_id"]) for row in tables["text_spans"])
    status_counts = Counter(str(row["extraction_status"]) for row in tables["commentaries"])

    lines = [
        "# Thevaram Manual QA Samples",
        "",
        f"- Table root: `{root}`",
        f"- Sample count: `{sample_count}`",
        "",
        "## Corpus Counts",
        "",
    ]
    for table_name, rows in tables.items():
        lines.append(f"- `{table_name}`: `{len(rows)}`")

    lines.extend(["", "## Commentary Status", ""])
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")

    lines.extend(["", "## Automated Audit Snapshot", ""])
    if audit["issue_counts"]:
        for severity, count in audit["issue_counts"].items():
            lines.append(f"- `{severity}`: `{count}`")
        for code, count in audit["code_counts"].items():
            lines.append(f"- `{code}`: `{count}`")
    else:
        lines.append("- No automated issues.")

    lines.extend(
        [
            "",
            "## What To Check In Each Sample",
            "",
            "- Thirumurai number and author are plausible.",
            "- Thogupu title, thalam, and pann are split correctly.",
            "- `global_song_no`, `source_song_no`, `local_song_no`, and `verse_index_in_thogupu` make sense.",
            "- Paadal text has meaningful line breaks and no UI/header/footer text.",
            "- Commentary status matches available `kurippurai` / `pozhppurai` text.",
            "- Source URL points to TamilVU and can be cited.",
            "",
            "## 20 Row QA Samples",
            "",
        ]
    )

    for index, paadal in enumerate(sample_paadalgal(tables["paadalgal"], sample_count), start=1):
        thogupu = thogupu_by_id.get(paadal["thogupu_id"], {})
        commentary = commentary_by_paadal.get(paadal["paadal_id"], {})
        lines.extend(
            [
                f"### Sample {index}: `{paadal['paadal_id']}`",
                "",
                f"- Thirumurai: `{paadal['thirumurai_no']}`",
                f"- Thogupu: `{paadal['thogupu_id']}`",
                f"- Title: {thogupu.get('title', '')}",
                f"- Thalam: {thogupu.get('paadapatta_thalam', '')}",
                f"- Pann: {thogupu.get('pann', '')}",
                f"- Song numbers: global `{paadal['global_song_no']}`, source `{paadal.get('source_song_no', paadal['global_song_no'])}`, local `{paadal['local_song_no']}`, index `{paadal['verse_index_in_thogupu']}`",
                f"- Commentary status: `{commentary.get('extraction_status', 'missing')}`",
                f"- Span count: `{spans_by_parent[str(paadal['paadal_id'])]}`",
                f"- Source: {paadal['source_url']}",
                "",
                "Paadal:",
                "",
                f"> {compact_text(str(paadal['paadal_text']))}",
                "",
            ]
        )
        if commentary.get("kurippurai") or commentary.get("pozhppurai"):
            lines.extend(
                [
                    "Commentary sample:",
                    "",
                    f"> {compact_text(str(commentary.get('kurippurai') or commentary.get('pozhppurai')), 220)}",
                    "",
                ]
            )

    duplicate_groups = duplicate_source_song_samples(tables["paadalgal"])
    lines.extend(["", "## Source Numbering Anomalies For Manual Review", ""])
    if not duplicate_groups:
        lines.append("- None")
    for rows in duplicate_groups:
        first = rows[0]
        lines.append(f"### Thirumurai {first['thirumurai_no']} source song `{first.get('source_song_no', first['global_song_no'])}`")
        lines.append("")
        for row in rows:
            lines.append(
                f"- `{row['paadal_id']}` local `{row['local_song_no']}` index `{row['verse_index_in_thogupu']}`: "
                f"{compact_text(str(row['paadal_text']), 160)}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a manual QA sample report for Thevaram tables.")
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-count", type=int, default=20)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(args.table_root, args.sample_count), encoding="utf-8")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
