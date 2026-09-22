from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PHASE1_VERSION = "saanrugraph-thevaram-1-7-freeze-v1"
PHASE2_VERSION = "saanrugraph-thevaram-1-7-phase2-cleaned-v1"
DEFAULT_NORMALIZED_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_V5_PRIMARY_EXPORT = Path(
    "data/exports/thevaram_pozhippurai_v5_supervisor_share_20260726/"
    "main_table_v5_auto_hardened_primary_clean_full_context.csv"
)
DEFAULT_OUTPUT_ROOT = Path("data/processed/saanrugraph_phase2")
DEFAULT_REPORT_PATH = Path("docs/research/saanrugraph_phase2_data_cleaning.md")

MAIN_SCOPE_THIRUMURAI = set(range(1, 8))
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
TOKEN_RE = re.compile(r"[\u0B80-\u0BFF0-9௦-௯A-Za-z]+")
ARABIC_OR_TAMIL_DIGITS_RE = re.compile(r"^[0-9௦-௯]+$")
PUNCT_SPACE_RE = re.compile(r"^[\s,.;:!?()\[\]{}\"'“”‘’\-–—/\\|]+$")

TAMIL_NUMBER_WORDS = {
    "பூஜ்யம்",
    "சுழியம்",
    "ஒன்று",
    "ஒரு",
    "ஓர்",
    "இரண்டு",
    "மூன்று",
    "நான்கு",
    "ஐந்து",
    "ஆறு",
    "ஏழு",
    "எட்டு",
    "ஒன்பது",
    "பத்து",
    "பதினொன்று",
    "பன்னிரண்டு",
    "பதின்மூன்று",
    "பதினான்கு",
    "பதினைந்து",
    "பதினாறு",
    "பதினேழு",
    "பதினெட்டு",
    "பத்தொன்பது",
    "இருபது",
}

GENERIC_SHORT_TOKENS = {
    "உடைய",
    "என்",
    "தன்",
    "தம்",
    "நம்",
    "அது",
    "இது",
    "அவன்",
    "இவன்",
    "அவர்",
    "இவர்",
    "ஆக",
    "ஆகிய",
    "என",
    "என்று",
    "என்னும்",
}


@dataclass(frozen=True)
class TextQuality:
    status: str
    flags: tuple[str, ...]
    token_count: int
    tamil_char_count: int
    normalized_text: str


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    return " ".join(text.strip().split())


def tokens(value: Any) -> list[str]:
    return TOKEN_RE.findall(normalize_text(value))


def tamil_char_count(value: Any) -> int:
    return len(TAMIL_RE.findall(str(value or "")))


def is_punctuation_only(value: Any) -> bool:
    text = str(value or "")
    return not normalize_text(text) or bool(PUNCT_SPACE_RE.fullmatch(text))


def is_numeric_token(token: str) -> bool:
    token = normalize_text(token).strip(".,;:!?()[]{}")
    return bool(token) and (
        bool(ARABIC_OR_TAMIL_DIGITS_RE.fullmatch(token)) or token in TAMIL_NUMBER_WORDS
    )


def is_numeric_only(value: Any) -> bool:
    row_tokens = tokens(value)
    return bool(row_tokens) and all(is_numeric_token(token) for token in row_tokens)


def classify_text_quality(value: Any, *, allow_single_token: bool = True) -> TextQuality:
    normalized = normalize_text(value)
    row_tokens = tokens(normalized)
    tamil_chars = tamil_char_count(normalized)
    flags: list[str] = []

    if not normalized:
        return TextQuality("reject", ("empty",), 0, 0, normalized)
    if is_punctuation_only(normalized):
        return TextQuality("reject", ("punctuation_only",), len(row_tokens), tamil_chars, normalized)
    if is_numeric_only(normalized):
        return TextQuality("reject", ("numeric_only",), len(row_tokens), tamil_chars, normalized)
    if tamil_chars == 0:
        return TextQuality("reject", ("no_tamil_text",), len(row_tokens), tamil_chars, normalized)
    if tamil_chars < 2:
        return TextQuality("reject", ("too_few_tamil_chars",), len(row_tokens), tamil_chars, normalized)

    if len(row_tokens) == 1:
        token = row_tokens[0]
        if token in GENERIC_SHORT_TOKENS:
            return TextQuality(
                "reject",
                ("generic_single_token",),
                len(row_tokens),
                tamil_chars,
                normalized,
            )
        if allow_single_token:
            flags.append("short_but_valid_single_token")
        else:
            return TextQuality("reject", ("single_token_not_allowed",), 1, tamil_chars, normalized)
    elif len(row_tokens) <= 2:
        flags.append("very_short_span")

    return TextQuality("keep", tuple(flags) or ("clean",), len(row_tokens), tamil_chars, normalized)


def parse_int(value: Any) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(str(value))
    except ValueError:
        return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def get_thirumurai_from_paadal_id(paadal_id: str) -> int | None:
    match = re.search(r"thirumurai_(\d+)_", paadal_id or "")
    return int(match.group(1)) if match else None


def substring_matches(parent_text: str, span_text: str, start: int | None, end: int | None) -> bool:
    if start is None or end is None:
        return False
    if start < 0 or end < start or end > len(parent_text):
        return False
    return parent_text[start:end] == span_text


def build_clean_span_rows(
    *,
    spans: list[dict[str, Any]],
    paadal_by_id: dict[str, dict[str, Any]],
    commentaries_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    paadal_span_rows: list[dict[str, Any]] = []
    commentary_span_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()

    for span in spans:
        parent_id = str(span.get("parent_id", ""))
        field_name = str(span.get("field_name", ""))
        span_text = str(span.get("text", ""))
        quality = classify_text_quality(span_text)
        start = parse_int(span.get("start_char"))
        end = parse_int(span.get("end_char"))

        if field_name in {"kurippurai", "pozhppurai"}:
            paadal_id = parent_id.removesuffix("_commentary")
            commentary_id = (
                parent_id if parent_id.endswith("_commentary") else f"{paadal_id}_commentary"
            )
            parent = commentaries_by_id.get(commentary_id, {})
            parent_text = str(parent.get(field_name, ""))
            node_kind = "commentary_span"
        else:
            paadal_id = parent_id
            parent = paadal_by_id.get(parent_id, {})
            parent_text = str(parent.get(field_name, ""))
            node_kind = "paadal_span"

        thirumurai_no = paadal_by_id.get(paadal_id, {}).get("thirumurai_no")
        if thirumurai_no not in MAIN_SCOPE_THIRUMURAI:
            counters["excluded_not_main_scope"] += 1
            continue

        bounds_match = substring_matches(parent_text, span_text, start, end)
        flags = list(quality.flags)
        if not bounds_match:
            flags.append("offset_mismatch")
        status = "keep" if quality.status == "keep" and bounds_match else "reject"
        counters[f"{node_kind}_{status}"] += 1
        for flag in flags:
            counters[f"flag_{flag}"] += 1

        row = {
            "dataset_version": PHASE2_VERSION,
            "span_id": span.get("span_id"),
            "parent_id": parent_id,
            "paadal_id": paadal_id,
            "thirumurai_no": thirumurai_no,
            "field_name": field_name,
            "span_type": span.get("span_type"),
            "start_char": start,
            "end_char": end,
            "text": span_text,
            "normalized_text": quality.normalized_text,
            "token_count": quality.token_count,
            "tamil_char_count": quality.tamil_char_count,
            "quality_status": status,
            "quality_flags": "|".join(flags),
            "offsets_match_parent": bounds_match,
            "in_pacolink_scope": field_name in {"paadal_text", "pozhppurai"},
        }

        if status != "keep" or flags != ["clean"]:
            issue_rows.append(
                {
                    "issue_scope": node_kind,
                    "record_id": span.get("span_id"),
                    "paadal_id": paadal_id,
                    "thirumurai_no": thirumurai_no,
                    "field_name": field_name,
                    "issue_flags": "|".join(flags),
                    "quality_status": status,
                    "text": span_text,
                }
            )

        if node_kind == "paadal_span" and status == "keep":
            paadal_span_rows.append(row)
        elif node_kind == "commentary_span" and status == "keep":
            commentary_span_rows.append(row)

    return paadal_span_rows, commentary_span_rows, issue_rows, dict(counters)


def hierarchy_validation(
    *,
    books: list[dict[str, Any]],
    thogupugal: list[dict[str, Any]],
    paadalgal: list[dict[str, Any]],
    commentaries: list[dict[str, Any]],
    spans: list[dict[str, Any]],
) -> dict[str, Any]:
    thirumurai_ids = {row.get("thirumurai_no") for row in books}
    thogupu_ids = {row.get("thogupu_id") for row in thogupugal}
    paadal_ids = {row.get("paadal_id") for row in paadalgal}
    commentary_ids = {row.get("commentary_id") for row in commentaries}
    duplicate_span_ids = [
        span_id for span_id, count in Counter(row.get("span_id") for row in spans).items() if count > 1
    ]

    missing_book_for_thogupu = [
        row.get("thogupu_id")
        for row in thogupugal
        if row.get("thirumurai_no") in MAIN_SCOPE_THIRUMURAI and row.get("thirumurai_no") not in thirumurai_ids
    ]
    missing_thogupu_for_paadal = [
        row.get("paadal_id")
        for row in paadalgal
        if row.get("thirumurai_no") in MAIN_SCOPE_THIRUMURAI and row.get("thogupu_id") not in thogupu_ids
    ]
    missing_paadal_for_commentary = [
        row.get("commentary_id")
        for row in commentaries
        if get_thirumurai_from_paadal_id(str(row.get("paadal_id", ""))) in MAIN_SCOPE_THIRUMURAI
        and row.get("paadal_id") not in paadal_ids
    ]
    missing_parent_for_span = []
    for row in spans:
        parent_id = str(row.get("parent_id", ""))
        field_name = str(row.get("field_name", ""))
        paadal_id = parent_id.removesuffix("_commentary") if parent_id.endswith("_commentary") else parent_id
        if get_thirumurai_from_paadal_id(paadal_id) not in MAIN_SCOPE_THIRUMURAI:
            continue
        if field_name in {"kurippurai", "pozhppurai"}:
            commentary_id = parent_id if parent_id.endswith("_commentary") else f"{paadal_id}_commentary"
            if commentary_id not in commentary_ids:
                missing_parent_for_span.append(row.get("span_id"))
        elif parent_id.endswith("_commentary") and parent_id not in commentary_ids:
            missing_parent_for_span.append(row.get("span_id"))
        elif not parent_id.endswith("_commentary") and parent_id not in paadal_ids:
            missing_parent_for_span.append(row.get("span_id"))

    issue_counts = {
        "missing_book_for_thogupu": len(missing_book_for_thogupu),
        "missing_thogupu_for_paadal": len(missing_thogupu_for_paadal),
        "missing_paadal_for_commentary": len(missing_paadal_for_commentary),
        "missing_parent_for_span": len(missing_parent_for_span),
        "duplicate_span_ids": len(duplicate_span_ids),
    }
    return {
        "status": "VALID" if not any(issue_counts.values()) else "NEEDS_REVIEW",
        "issue_counts": issue_counts,
        "samples": {
            "missing_book_for_thogupu": missing_book_for_thogupu[:20],
            "missing_thogupu_for_paadal": missing_thogupu_for_paadal[:20],
            "missing_paadal_for_commentary": missing_paadal_for_commentary[:20],
            "missing_parent_for_span": missing_parent_for_span[:20],
            "duplicate_span_ids": duplicate_span_ids[:20],
        },
    }


def classify_link_candidate(row: dict[str, str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    thirumurai_no = parse_int(row.get("thirumurai_no"))
    if thirumurai_no not in MAIN_SCOPE_THIRUMURAI:
        reasons.append("not_main_scope_thirumurai_1_7")

    if row.get("source_field") != "paadal_text":
        reasons.append("source_field_not_paadal_text")
    if row.get("target_field") != "pozhppurai":
        reasons.append("target_field_not_pozhippurai")

    source_quality = classify_text_quality(row.get("source_text", ""))
    target_quality = classify_text_quality(row.get("target_text", ""))
    if source_quality.status != "keep":
        reasons.extend(f"source_{flag}" for flag in source_quality.flags)
    if target_quality.status != "keep":
        reasons.extend(f"target_{flag}" for flag in target_quality.flags)

    source_start = parse_int(row.get("source_start_char"))
    source_end = parse_int(row.get("source_end_char"))
    target_start = parse_int(row.get("target_start_char"))
    target_end = parse_int(row.get("target_end_char"))
    if not substring_matches(
        str(row.get("full_paadal_text", "")),
        str(row.get("source_text", "")),
        source_start,
        source_end,
    ):
        reasons.append("source_offset_mismatch")
    if not substring_matches(
        str(row.get("full_pozhippurai", "")),
        str(row.get("target_text", "")),
        target_start,
        target_end,
    ):
        reasons.append("target_offset_mismatch")

    return ("keep" if not reasons else "reject"), reasons


def build_candidate_pool(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    short_flag_count = 0

    keep_fields = [
        "link_id",
        "paadal_id",
        "commentary_id",
        "thirumurai_no",
        "pathigam_id",
        "hymn_id",
        "confidence",
        "score",
        "manual_review_required",
        "relationship_type",
        "source_field",
        "source_text",
        "source_start_char",
        "source_end_char",
        "target_field",
        "target_text",
        "target_start_char",
        "target_end_char",
        "issue_tags_after",
        "penalties_applied",
        "repair_actions_applied",
        "diagnostic_note",
    ]

    for row in rows:
        status, reasons = classify_link_candidate(row)
        if status == "keep":
            source_quality = classify_text_quality(row.get("source_text", ""))
            target_quality = classify_text_quality(row.get("target_text", ""))
            quality_flags = sorted(set(source_quality.flags + target_quality.flags) - {"clean"})
            if quality_flags:
                short_flag_count += 1
            kept.append(
                {
                    "dataset_version": PHASE2_VERSION,
                    "phase1_dataset_version": PHASE1_VERSION,
                    "candidate_status": "clean_candidate",
                    "quality_flags": "|".join(quality_flags) if quality_flags else "clean",
                    **{field: row.get(field, "") for field in keep_fields},
                }
            )
        else:
            for reason in reasons:
                reason_counts[reason] += 1
            excluded.append(
                {
                    "link_id": row.get("link_id", ""),
                    "paadal_id": row.get("paadal_id", ""),
                    "commentary_id": row.get("commentary_id", ""),
                    "thirumurai_no": row.get("thirumurai_no", ""),
                    "confidence": row.get("confidence", ""),
                    "relationship_type": row.get("relationship_type", ""),
                    "source_text": row.get("source_text", ""),
                    "target_text": row.get("target_text", ""),
                    "exclusion_reasons": "|".join(reasons),
                }
            )

    summary = {
        "input_v5_primary_rows": len(rows),
        "clean_candidate_rows": len(kept),
        "excluded_candidate_rows": len(excluded),
        "exclusion_reason_counts": dict(sorted(reason_counts.items())),
        "candidate_quality_flagged_rows": short_flag_count,
        "confidence_counts": dict(sorted(Counter(row["confidence"] for row in kept).items())),
        "relationship_counts": dict(sorted(Counter(row["relationship_type"] for row in kept).items())),
    }
    return kept, excluded, summary


def missing_commentary_rows(
    *,
    paadalgal: list[dict[str, Any]],
    commentaries_by_paadal_id: dict[str, dict[str, Any]],
    clean_candidate_pool: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    linked_paadal_ids = {row["paadal_id"] for row in clean_candidate_pool}
    report_rows: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    by_thirumurai: dict[int, Counter[str]] = defaultdict(Counter)

    for paadal in paadalgal:
        thirumurai_no = paadal.get("thirumurai_no")
        if thirumurai_no not in MAIN_SCOPE_THIRUMURAI:
            continue
        paadal_id = str(paadal.get("paadal_id", ""))
        commentary = commentaries_by_paadal_id.get(paadal_id, {})
        pozhppurai = normalize_text(commentary.get("pozhppurai", ""))
        if not pozhppurai:
            category = "true_missing_pozhippurai"
        elif paadal_id not in linked_paadal_ids:
            category = "usable_pozhippurai_but_no_clean_v5_link"
        else:
            continue

        category_counts[category] += 1
        by_thirumurai[int(thirumurai_no)][category] += 1
        report_rows.append(
            {
                "dataset_version": PHASE2_VERSION,
                "category": category,
                "paadal_id": paadal_id,
                "commentary_id": commentary.get("commentary_id", ""),
                "thirumurai_no": thirumurai_no,
                "pathigam_id": paadal.get("thogupu_id", ""),
                "global_song_no": paadal.get("global_song_no", ""),
                "source_url": paadal.get("source_url", ""),
                "commentary_url": paadal.get("commentary_url", ""),
                "paadal_text_preview": normalize_text(paadal.get("paadal_text", ""))[:180],
                "pozhppurai_char_count": len(pozhppurai),
                "explanation": (
                    "Missing from source/normalized commentary, not a linker error."
                    if category == "true_missing_pozhippurai"
                    else "Pozhippurai exists, but no clean v5 candidate link remains after Phase 2 filters."
                ),
            }
        )

    summary = {
        "rows": len(report_rows),
        "category_counts": dict(sorted(category_counts.items())),
        "by_thirumurai": {
            str(key): dict(sorted(value.items())) for key, value in sorted(by_thirumurai.items())
        },
    }
    return report_rows, summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    corpus = summary["corpus"]
    candidates = summary["candidate_pool"]
    missing = summary["missing_commentary"]
    hierarchy = summary["hierarchy_validation"]
    lines = [
        "# SaanruGraph Phase 2 Data Cleaning",
        "",
        f"Dataset version: `{PHASE2_VERSION}`",
        "",
        "## Scope",
        "",
        "Phase 2 keeps the Phase 1 paper boundary: Thevaram Thirumurai 1-7 only.",
        "Thirumurai 8 remains excluded from the main evaluation because it has no usable Pozhippurai coverage in the frozen tables.",
        "",
        "## Cleaned Output Files",
        "",
        "| Output | Path |",
        "| --- | --- |",
        "| Cleaned paadal spans | `data/processed/saanrugraph_phase2/cleaned_paadal_spans.csv` |",
        "| Cleaned commentary spans | `data/processed/saanrugraph_phase2/cleaned_commentary_spans.csv` |",
        "| Missing commentary report | `data/processed/saanrugraph_phase2/missing_commentary_report.csv` |",
        "| Final link candidate pool | `data/processed/saanrugraph_phase2/final_link_candidate_pool.csv` |",
        "| Excluded link candidates | `data/processed/saanrugraph_phase2/excluded_link_candidates.csv` |",
        "| Span quality issues | `data/processed/saanrugraph_phase2/span_quality_issues.csv` |",
        "| Hierarchy validation | `data/processed/saanrugraph_phase2/hierarchy_validation_report.json` |",
        "| Machine summary | `data/processed/saanrugraph_phase2/phase2_cleaning_summary.json` |",
        "",
        "## Frozen Corpus After Cleaning",
        "",
        f"- Paadal rows in scope: `{corpus['paadal_rows_1_7']}`",
        f"- Raw paadal line spans in scope: `{corpus['raw_paadal_line_spans_1_7']}`",
        f"- Cleaned paadal spans kept: `{corpus['cleaned_paadal_spans']}`",
        f"- Cleaned commentary spans kept: `{corpus['cleaned_commentary_spans']}`",
        f"- Cleaned Pozhippurai spans kept: `{corpus['cleaned_pozhippurai_spans']}`",
        f"- Cleaned Kurippurai spans kept: `{corpus['cleaned_kurippurai_spans']}`",
        "",
        "## Candidate Pool",
        "",
        f"- Input v5 primary rows: `{candidates['input_v5_primary_rows']}`",
        f"- Final clean candidate rows: `{candidates['clean_candidate_rows']}`",
        f"- Excluded candidate rows: `{candidates['excluded_candidate_rows']}`",
        f"- Flagged but retained short-span rows: `{candidates['candidate_quality_flagged_rows']}`",
        "",
        "Confidence distribution in the final candidate pool:",
        "",
        "| Confidence | Rows |",
        "| --- | ---: |",
    ]
    for label, count in candidates["confidence_counts"].items():
        lines.append(f"| `{label}` | {count:,} |")
    lines.extend(
        [
            "",
            "Excluded candidate reasons:",
            "",
            "| Reason | Rows |",
            "| --- | ---: |",
        ]
    )
    for reason, count in candidates["exclusion_reason_counts"].items():
        lines.append(f"| `{reason}` | {count:,} |")
    if not candidates["exclusion_reason_counts"]:
        lines.append("| None | 0 |")

    lines.extend(
        [
            "",
            "## Missing Commentary Separation",
            "",
            "Rows with empty Pozhippurai are classified as true missing-commentary coverage, not linker failure.",
            "",
            "| Category | Rows |",
            "| --- | ---: |",
        ]
    )
    for category, count in missing["category_counts"].items():
        lines.append(f"| `{category}` | {count:,} |")

    lines.extend(
        [
            "",
            "## Hierarchy Validation",
            "",
            f"Status: `{hierarchy['status']}`",
            "",
            "| Check | Issues |",
            "| --- | ---: |",
        ]
    )
    for check, count in hierarchy["issue_counts"].items():
        lines.append(f"| `{check}` | {count:,} |")

    lines.extend(
        [
            "",
            "## Cleaning Rules Frozen For Phase 2",
            "",
            "- Remove numeric-only source or target spans from positive linking candidates.",
            "- Remove punctuation-only and empty spans.",
            "- Keep valid single-token Tamil spans, but mark them with `short_but_valid_single_token`.",
            "- Exclude non-Pozhippurai target links from the main Paadal-Pozhippurai candidate pool.",
            "- Verify source and target character offsets against the full Paadal and Pozhippurai text.",
            "- Keep true missing-commentary cases in a separate report.",
            "",
            "## Phase 2 Acceptance",
            "",
            "Phase 2 is accepted when the cleaned span tables, missing-commentary report, final candidate pool, and validation summary are produced without overwriting v3/v4/v5 outputs.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_phase2(
    *,
    normalized_root: Path = DEFAULT_NORMALIZED_ROOT,
    v5_primary_export: Path = DEFAULT_V5_PRIMARY_EXPORT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> dict[str, Any]:
    books = read_jsonl(normalized_root / "thirumurai_books.jsonl")
    thogupugal = read_jsonl(normalized_root / "paadal_thogupugal.jsonl")
    paadalgal = read_jsonl(normalized_root / "paadalgal.jsonl")
    commentaries = read_jsonl(normalized_root / "commentaries.jsonl")
    spans = read_jsonl(normalized_root / "text_spans.jsonl")
    v5_rows = read_csv(v5_primary_export)

    paadal_by_id = {str(row.get("paadal_id", "")): row for row in paadalgal}
    commentaries_by_id = {str(row.get("commentary_id", "")): row for row in commentaries}
    commentaries_by_paadal_id = {str(row.get("paadal_id", "")): row for row in commentaries}

    hierarchy = hierarchy_validation(
        books=books,
        thogupugal=thogupugal,
        paadalgal=paadalgal,
        commentaries=commentaries,
        spans=spans,
    )
    paadal_spans, commentary_spans, span_issues, span_summary = build_clean_span_rows(
        spans=spans,
        paadal_by_id=paadal_by_id,
        commentaries_by_id=commentaries_by_id,
    )
    candidate_pool, excluded_candidates, candidate_summary = build_candidate_pool(v5_rows)
    missing_rows, missing_summary = missing_commentary_rows(
        paadalgal=paadalgal,
        commentaries_by_paadal_id=commentaries_by_paadal_id,
        clean_candidate_pool=candidate_pool,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    write_csv(output_root / "cleaned_paadal_spans.csv", paadal_spans)
    write_jsonl(output_root / "cleaned_paadal_spans.jsonl", paadal_spans)
    write_csv(output_root / "cleaned_commentary_spans.csv", commentary_spans)
    write_jsonl(output_root / "cleaned_commentary_spans.jsonl", commentary_spans)
    write_csv(output_root / "missing_commentary_report.csv", missing_rows)
    write_jsonl(output_root / "missing_commentary_report.jsonl", missing_rows)
    write_csv(output_root / "final_link_candidate_pool.csv", candidate_pool)
    write_jsonl(output_root / "final_link_candidate_pool.jsonl", candidate_pool)
    write_csv(output_root / "excluded_link_candidates.csv", excluded_candidates)
    write_csv(output_root / "span_quality_issues.csv", span_issues)
    write_json(output_root / "hierarchy_validation_report.json", hierarchy)

    corpus_summary = {
        "paadal_rows_1_7": sum(1 for row in paadalgal if row.get("thirumurai_no") in MAIN_SCOPE_THIRUMURAI),
        "raw_paadal_line_spans_1_7": sum(
            1
            for row in spans
            if row.get("field_name") == "paadal_text"
            and get_thirumurai_from_paadal_id(str(row.get("parent_id", ""))) in MAIN_SCOPE_THIRUMURAI
        ),
        "cleaned_paadal_spans": len(paadal_spans),
        "cleaned_commentary_spans": len(commentary_spans),
        "cleaned_pozhippurai_spans": sum(1 for row in commentary_spans if row["field_name"] == "pozhppurai"),
        "cleaned_kurippurai_spans": sum(1 for row in commentary_spans if row["field_name"] == "kurippurai"),
        "span_quality_summary": span_summary,
    }
    summary = {
        "dataset_version": PHASE2_VERSION,
        "phase1_dataset_version": PHASE1_VERSION,
        "scope": "Thevaram Thirumurai 1-7 only",
        "excluded_from_main_evaluation": {
            "thirumurai_8": "No usable Pozhippurai spans in the frozen normalized tables."
        },
        "input_artifacts": {
            "normalized_root": str(normalized_root),
            "v5_primary_export": str(v5_primary_export),
        },
        "output_artifacts": {
            "output_root": str(output_root),
            "report": str(report_path),
        },
        "corpus": corpus_summary,
        "candidate_pool": candidate_summary,
        "missing_commentary": missing_summary,
        "hierarchy_validation": hierarchy,
    }
    write_json(output_root / "phase2_cleaning_summary.json", summary)
    write_report(report_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SaanruGraph Phase 2 cleaned data artifacts.")
    parser.add_argument("--normalized-root", type=Path, default=DEFAULT_NORMALIZED_ROOT)
    parser.add_argument("--v5-primary-export", type=Path, default=DEFAULT_V5_PRIMARY_EXPORT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()
    summary = build_phase2(
        normalized_root=args.normalized_root,
        v5_primary_export=args.v5_primary_export,
        output_root=args.output_root,
        report_path=args.report_path,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
