from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspector.site_inspector import snapshot_filename
from scraper.pilot_hymn_scraper import parse_hymn_page

CORPUS_PATH = Path("data/processed/corpus/irandaam_thirumurai.jsonl")
RAW_HYMN_DIR = Path("data/raw/corpus/irandaam_thirumurai/hymns")
RAW_COMMENTARY_DIR = Path("data/raw/corpus/irandaam_thirumurai/commentary")
AUDIT_REPORT = Path("reports/corpus-audit-report.md")
SCHEMA_REPORT = Path("reports/schema-validation-report.md")
COVERAGE_REPORT = Path("reports/corpus-coverage-report.md")
MANUAL_SAMPLE_REPORT = Path("reports/manual-audit-sample.md")
MANIFEST_PATH = Path("corpus_manifest.json")
FREEZE_DOC = Path("docs/corpus-freeze-v1.md")

POZH_LABEL_RE = re.compile(r"(?:பொழிப்புரை|பொ-ரை)\s*[:;]")
KURI_LABEL_RE = re.compile(r"(?:குறிப்புரை|கு-ரை)\s*[:;]")
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")

REQUIRED_FIELDS = {
    "record_type": str,
    "source": str,
    "source_site": str,
    "language": str,
    "domain": str,
    "genre": str,
    "religious_tradition": str,
    "collection": str,
    "work": str,
    "thirumurai": str,
    "thirumurai_number": int,
    "author": str,
    "hymn_id": str,
    "hymn_title": str,
    "hymn_location": str,
    "hymn_note": str,
    "pann": str,
    "song_no": str,
    "verse_index_in_hymn": int,
    "verse_text": str,
    "commentary_available": bool,
    "pozhppurai": str,
    "kurippurai": str,
    "hymn_url": str,
    "commentary_url": str,
    "source_parameters": dict,
    "text_statistics": dict,
    "extraction_metadata": dict,
}


@dataclass(slots=True)
class PartialAudit:
    hymn_id: str
    hymn_title: str
    song_no: str
    commentary_url: str
    missing_fields: list[str]
    source_contains: dict[str, bool]
    parser_extracted: dict[str, bool]
    root_cause: str
    classification: str
    recommended_action: str


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commentary_snapshot_text(url: str) -> str:
    path = RAW_COMMENTARY_DIR / snapshot_filename(url)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def hymn_snapshot_text(url: str) -> str:
    path = RAW_HYMN_DIR / snapshot_filename(url)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def qparams(url: str) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items() if values}


def tamil_ratio(text: str) -> float:
    visible = "".join(ch for ch in text if not ch.isspace())
    return len(TAMIL_RE.findall(visible)) / len(visible) if visible else 0.0


def percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return float(ordered[index])


def validate_schema(records: list[dict]) -> dict:
    violations: list[str] = []
    missing_required: list[str] = []
    invalid_types: list[str] = []
    malformed_records: list[str] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            malformed_records.append(f"record {index} is not an object")
            continue
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in record:
                msg = f"record {index} missing {field}"
                missing_required.append(msg)
                violations.append(msg)
                continue
            if not isinstance(record[field], expected_type):
                msg = f"record {index} field {field} expected {expected_type.__name__}, got {type(record[field]).__name__}"
                invalid_types.append(msg)
                violations.append(msg)
    return {
        "schema_violations": violations,
        "missing_required_fields": missing_required,
        "invalid_field_types": invalid_types,
        "malformed_records": malformed_records,
    }


def integrity_validation(records: list[dict]) -> dict:
    song_counts = Counter(r.get("song_no") for r in records if r.get("song_no"))
    commentary_url_counts = Counter(r.get("commentary_url") for r in records if r.get("commentary_url"))
    hymn_url_to_ids: dict[str, set[str]] = defaultdict(set)
    empty_strings = []
    null_values = []
    status_inconsistency = []
    metadata_issues = []
    source_param_issues = []
    song_mismatches = []
    hymn_mismatches = []
    corrupt_tamil = []
    unusual_non_tamil = []
    short_verses = []
    short_commentary = []

    for index, record in enumerate(records, start=1):
        for key, value in record.items():
            if value is None:
                null_values.append(f"record {index} {key}")
            if isinstance(value, str) and value == "" and key not in {"hymn_note", "pann", "pozhppurai", "kurippurai"}:
                empty_strings.append(f"record {index} {key}")
        if record.get("hymn_url") and record.get("hymn_id"):
            hymn_url_to_ids[record["hymn_url"]].add(record["hymn_id"])

        params = record.get("source_parameters", {})
        metadata = record.get("extraction_metadata", {})
        if not isinstance(params, dict) or not {"subid", "sub_id", "song_no"}.issubset(params):
            source_param_issues.append(f"record {index} malformed source_parameters")
        if not isinstance(metadata, dict) or "extraction_status" not in metadata:
            metadata_issues.append(f"record {index} malformed extraction_metadata")

        status = metadata.get("extraction_status") if isinstance(metadata, dict) else ""
        missing_commentary = not record.get("pozhppurai") or not record.get("kurippurai")
        if status == "success" and missing_commentary:
            status_inconsistency.append(f"record {index} success but commentary field missing")
        if status != "success" and not missing_commentary:
            status_inconsistency.append(f"record {index} non-success but commentary complete")

        cparams = qparams(record.get("commentary_url", ""))
        if cparams.get("song_no") and cparams["song_no"] != record.get("song_no"):
            song_mismatches.append(f"{record.get('hymn_id')}:{record.get('song_no')} url_song_no={cparams['song_no']}")
        if cparams.get("sub_id") and cparams["sub_id"] != record.get("hymn_id"):
            hymn_mismatches.append(f"{record.get('hymn_id')}:{record.get('song_no')} url_sub_id={cparams['sub_id']}")

        verse = record.get("verse_text", "")
        commentary = f"{record.get('pozhppurai', '')} {record.get('kurippurai', '')}".strip()
        if tamil_ratio(verse) < 0.45:
            corrupt_tamil.append(f"{record.get('hymn_id')}:{record.get('song_no')} low verse Tamil ratio")
        if commentary and tamil_ratio(commentary) < 0.35:
            unusual_non_tamil.append(f"{record.get('hymn_id')}:{record.get('song_no')} low commentary Tamil ratio")
        if len(verse) < 25:
            short_verses.append(f"{record.get('hymn_id')}:{record.get('song_no')} verse_chars={len(verse)}")
        if commentary and len(commentary) < 40:
            short_commentary.append(f"{record.get('hymn_id')}:{record.get('song_no')} commentary_chars={len(commentary)}")

    return {
        "total_records": len(records),
        "total_unique_hymns": len({r.get("hymn_id") for r in records}),
        "total_unique_song_no": len({r.get("song_no") for r in records}),
        "duplicate_song_no": sorted(k for k, v in song_counts.items() if v > 1),
        "duplicate_hymn_urls": sorted(url for url, hymn_ids in hymn_url_to_ids.items() if len(hymn_ids) > 1),
        "duplicate_commentary_urls": sorted(k for k, v in commentary_url_counts.items() if v > 1),
        "missing_verse_text": sum(not r.get("verse_text") for r in records),
        "missing_commentary_urls": sum(not r.get("commentary_url") for r in records),
        "missing_pozhppurai": sum(not r.get("pozhppurai") for r in records),
        "missing_kurippurai": sum(not r.get("kurippurai") for r in records),
        "empty_strings": empty_strings,
        "null_values": null_values,
        "status_inconsistency": status_inconsistency,
        "inconsistent_metadata": metadata_issues,
        "malformed_source_parameters": source_param_issues,
        "song_no_mismatch_with_commentary_url": song_mismatches,
        "hymn_id_mismatch_with_commentary_url": hymn_mismatches,
        "corrupted_tamil_text": corrupt_tamil,
        "unusual_non_tamil_content": unusual_non_tamil,
        "suspiciously_short_verse_text": short_verses,
        "suspiciously_short_commentary": short_commentary,
    }


def audit_partials(records: list[dict]) -> list[PartialAudit]:
    partials = [r for r in records if r.get("extraction_metadata", {}).get("extraction_status") != "success"]
    audits: list[PartialAudit] = []
    for record in partials:
        html = commentary_snapshot_text(record["commentary_url"])
        missing = []
        if not record.get("pozhppurai"):
            missing.append("pozhppurai")
        if not record.get("kurippurai"):
            missing.append("kurippurai")
        source_contains = {
            "pozhppurai": bool(POZH_LABEL_RE.search(html)),
            "kurippurai": bool(KURI_LABEL_RE.search(html)),
        }
        parser_extracted = {
            "pozhppurai": bool(record.get("pozhppurai")),
            "kurippurai": bool(record.get("kurippurai")),
        }
        if not html:
            classification = "UNKNOWN"
            root = "raw commentary snapshot was not found"
            action = "Locate or refetch raw snapshot in a separate repair phase."
        elif all(not source_contains[field] for field in missing):
            classification = "SOURCE_MISSING"
            root = "the expected commentary section label is absent from the saved source HTML"
            action = "Human review TamilVU page; accept partial record if source truly omits section."
        elif any(source_contains[field] and not parser_extracted[field] for field in missing):
            classification = "PARSER_LIMITATION"
            root = "source appears to contain the field but parser did not extract it"
            action = "Create a focused parser repair fixture before changing records."
        elif "<html" not in html.lower():
            classification = "CORRUPT_HTML"
            root = "snapshot does not look like an HTML document"
            action = "Inspect raw snapshot and recapture source in a separate repair phase."
        else:
            classification = "UNKNOWN"
            root = "missing field cause could not be proven from automated checks"
            action = "Manual source comparison required."

        audits.append(
            PartialAudit(
                hymn_id=record["hymn_id"],
                hymn_title=record["hymn_title"],
                song_no=record["song_no"],
                commentary_url=record["commentary_url"],
                missing_fields=missing,
                source_contains=source_contains,
                parser_extracted=parser_extracted,
                root_cause=root,
                classification=classification,
                recommended_action=action,
            )
        )
    return audits


def coverage_validation(records: list[dict]) -> dict:
    by_hymn: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_hymn[record["hymn_id"]].append(record)
    hymn_ids = sorted(by_hymn, key=int)
    sample_ids = sorted(set(hymn_ids[:10] + hymn_ids[len(hymn_ids)//2-5:len(hymn_ids)//2+5] + hymn_ids[-10:]), key=int)
    rows = []
    for hymn_id in sample_ids:
        extracted = by_hymn[hymn_id]
        html = hymn_snapshot_text(extracted[0]["hymn_url"])
        source_count = None
        missing = []
        extra = []
        if html:
            _title, source_verses = parse_hymn_page(extracted[0]["hymn_url"], html)
            source_song = {v.song_no for v in source_verses}
            extracted_song = {r["song_no"] for r in extracted}
            source_count = len(source_verses)
            missing = sorted(source_song - extracted_song)
            extra = sorted(extracted_song - source_song)
        rows.append({
            "hymn_id": hymn_id,
            "hymn_title": extracted[0]["hymn_title"],
            "source_verse_count": source_count,
            "extracted_verse_count": len(extracted),
            "missing_verses": missing,
            "extra_verses": extra,
            "coverage": (len(extracted) / source_count) if source_count else 0.0,
        })
    avg = statistics.mean(row["coverage"] for row in rows) if rows else 0.0
    return {"sample_rows": rows, "average_coverage": avg}


def corpus_statistics(records: list[dict]) -> dict:
    by_hymn = defaultdict(list)
    verse_lengths = []
    commentary_lengths = []
    verse_lines = []
    review = []
    for record in records:
        by_hymn[record["hymn_id"]].append(record)
        verse_lengths.append(len(record["verse_text"]))
        commentary_length = len(record.get("pozhppurai", "")) + len(record.get("kurippurai", ""))
        commentary_lengths.append(commentary_length)
        verse_lines.append(len([line for line in record["verse_text"].splitlines() if line.strip()]))
        if record.get("extraction_metadata", {}).get("extraction_status") != "success":
            review.append(record)
    counts = [len(items) for items in by_hymn.values()]
    return {
        "total_hymns": len(by_hymn),
        "total_verses": len(records),
        "average_verses_per_hymn": statistics.mean(counts) if counts else 0.0,
        "minimum_verses_per_hymn": min(counts) if counts else 0,
        "maximum_verses_per_hymn": max(counts) if counts else 0,
        "commentary_coverage_percentage": 100 * sum(bool(r.get("commentary_url")) for r in records) / len(records),
        "pozhppurai_coverage_percentage": 100 * sum(bool(r.get("pozhppurai")) for r in records) / len(records),
        "kurippurai_coverage_percentage": 100 * sum(bool(r.get("kurippurai")) for r in records) / len(records),
        "verse_length_distribution": {"min": min(verse_lengths), "p50": percentile(verse_lengths, 50), "p95": percentile(verse_lengths, 95), "max": max(verse_lengths)},
        "commentary_length_distribution": {"min": min(commentary_lengths), "p50": percentile(commentary_lengths, 50), "p95": percentile(commentary_lengths, 95), "max": max(commentary_lengths)},
        "verse_line_count_distribution": dict(sorted(Counter(verse_lines).items())),
        "top_unusual_records": sorted(records, key=lambda r: len(r.get("pozhppurai", "")) + len(r.get("kurippurai", "")))[:10],
        "records_requiring_human_review": review,
    }


def render_schema_report(schema: dict) -> str:
    return "\n".join([
        "# Schema Validation Report",
        "",
        f"- Schema violations: `{len(schema['schema_violations'])}`",
        f"- Missing required fields: `{len(schema['missing_required_fields'])}`",
        f"- Invalid field types: `{len(schema['invalid_field_types'])}`",
        f"- Malformed records: `{len(schema['malformed_records'])}`",
        "",
        "## Violations",
        "",
        *(f"- {item}" for item in schema["schema_violations"][:200]),
        "" if schema["schema_violations"] else "- None",
    ])


def render_coverage_report(coverage: dict) -> str:
    lines = [
        "# Corpus Coverage Report",
        "",
        f"- Sampled hymns: `{len(coverage['sample_rows'])}`",
        f"- Average sampled coverage: `{coverage['average_coverage']:.2%}`",
        "",
        "| Hymn ID | Source Verses | Extracted Verses | Coverage | Missing | Extra |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in coverage["sample_rows"]:
        lines.append(f"| `{row['hymn_id']}` | {row['source_verse_count']} | {row['extracted_verse_count']} | {row['coverage']:.2%} | {', '.join(row['missing_verses']) or 'none'} | {', '.join(row['extra_verses']) or 'none'} |")
    return "\n".join(lines)


def preview(text: str, limit: int = 180) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return text[:limit] + ("..." if len(text) > limit else "")


def render_manual_sample(records: list[dict]) -> str:
    rng = random.Random(20260607)
    sample = sorted(rng.sample(records, 20), key=lambda r: (int(r["hymn_id"]), int(r["song_no"])))
    lines = [
        "# Manual Audit Sample",
        "",
        "Random deterministic sample of 20 records for manual comparison against TamilVU.",
        "",
        "| Hymn ID | Hymn Title | Song No | Hymn URL | Commentary URL | Verse Preview | Pozhppurai Preview | Kurippurai Preview |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in sample:
        lines.append(f"| `{record['hymn_id']}` | {record['hymn_title'].replace('|', '\\|')} | `{record['song_no']}` | `{record['hymn_url']}` | `{record['commentary_url']}` | {preview(record['verse_text'])} | {preview(record.get('pozhppurai', ''))} | {preview(record.get('kurippurai', ''))} |")
    return "\n".join(lines)


def render_audit_report(records: list[dict], stats: dict, integrity: dict, schema: dict, coverage: dict, partials: list[PartialAudit]) -> str:
    freeze_ready = (
        not schema["schema_violations"]
        and not integrity["duplicate_song_no"]
        and not integrity["duplicate_commentary_urls"]
        and integrity["missing_verse_text"] == 0
        and coverage["average_coverage"] == 1.0
    )
    lines = [
        "# Corpus Audit Report",
        "",
        "## Executive Summary",
        "",
        f"- Corpus records audited: `{len(records)}`",
        f"- Unique hymns: `{stats['total_hymns']}`",
        f"- Partial commentary records: `{len(partials)}`",
        f"- Schema violations: `{len(schema['schema_violations'])}`",
        f"- Duplicate song_no: `{len(integrity['duplicate_song_no'])}`",
        f"- Coverage sample average: `{coverage['average_coverage']:.2%}`",
        f"- Freeze recommendation: `{'FREEZE_READY' if freeze_ready else 'REPAIR_REQUIRED'}`",
        "",
        "## Corpus Statistics",
        "",
        f"- Total hymns: `{stats['total_hymns']}`",
        f"- Total verses: `{stats['total_verses']}`",
        f"- Average verses per hymn: `{stats['average_verses_per_hymn']:.2f}`",
        f"- Minimum verses per hymn: `{stats['minimum_verses_per_hymn']}`",
        f"- Maximum verses per hymn: `{stats['maximum_verses_per_hymn']}`",
        f"- Commentary coverage: `{stats['commentary_coverage_percentage']:.2f}%`",
        f"- Pozhppurai coverage: `{stats['pozhppurai_coverage_percentage']:.2f}%`",
        f"- Kurippurai coverage: `{stats['kurippurai_coverage_percentage']:.2f}%`",
        f"- Verse length distribution: `{stats['verse_length_distribution']}`",
        f"- Commentary length distribution: `{stats['commentary_length_distribution']}`",
        f"- Verse line count distribution: `{stats['verse_line_count_distribution']}`",
        "",
        "## Integrity Validation",
        "",
        f"- Missing verse text: `{integrity['missing_verse_text']}`",
        f"- Missing commentary URLs: `{integrity['missing_commentary_urls']}`",
        f"- Missing pozhppurai: `{integrity['missing_pozhppurai']}`",
        f"- Missing kurippurai: `{integrity['missing_kurippurai']}`",
        f"- Duplicate song_no: `{len(integrity['duplicate_song_no'])}`",
        f"- Duplicate hymn URLs across hymn IDs: `{len(integrity['duplicate_hymn_urls'])}`",
        f"- Duplicate commentary URLs: `{len(integrity['duplicate_commentary_urls'])}`",
        f"- Song/commentary URL mismatches: `{len(integrity['song_no_mismatch_with_commentary_url'])}`",
        f"- Hymn/commentary URL mismatches: `{len(integrity['hymn_id_mismatch_with_commentary_url'])}`",
        f"- Null values: `{len(integrity['null_values'])}`",
        f"- Empty required strings: `{len(integrity['empty_strings'])}`",
        f"- Status inconsistencies: `{len(integrity['status_inconsistency'])}`",
        f"- Malformed source parameters: `{len(integrity['malformed_source_parameters'])}`",
        f"- Malformed extraction metadata: `{len(integrity['inconsistent_metadata'])}`",
        f"- Corrupted Tamil text signals: `{len(integrity['corrupted_tamil_text'])}`",
        f"- Unusual non-Tamil content signals: `{len(integrity['unusual_non_tamil_content'])}`",
        f"- Suspiciously short verses: `{len(integrity['suspiciously_short_verse_text'])}`",
        f"- Suspiciously short commentary: `{len(integrity['suspiciously_short_commentary'])}`",
        "",
        "## Schema Validation",
        "",
        f"- Schema violations: `{len(schema['schema_violations'])}`",
        f"- Missing required fields: `{len(schema['missing_required_fields'])}`",
        f"- Invalid field types: `{len(schema['invalid_field_types'])}`",
        "",
        "## Coverage Validation",
        "",
        f"- Sampled hymns: `{len(coverage['sample_rows'])}`",
        f"- Average coverage: `{coverage['average_coverage']:.2%}`",
        "",
        "## Partial Commentary Audit",
        "",
        "| Hymn ID | Song No | Missing | Source Contains Field | Parser Extracted | Classification | Action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in partials:
        lines.append(f"| `{item.hymn_id}` | `{item.song_no}` | {', '.join(item.missing_fields)} | {item.source_contains} | {item.parser_extracted} | `{item.classification}` | {item.recommended_action} |")
    lines.extend([
        "",
        "## Top Unusual Records",
        "",
        "These are the shortest total-commentary records, useful for manual spot checks.",
        "",
        "| Hymn ID | Song No | Commentary Chars | Status | URL |",
        "| --- | --- | ---: | --- | --- |",
    ])
    for record in stats["top_unusual_records"]:
        commentary_chars = len(record.get("pozhppurai", "")) + len(record.get("kurippurai", ""))
        status = record.get("extraction_metadata", {}).get("extraction_status", "")
        lines.append(f"| `{record['hymn_id']}` | `{record['song_no']}` | {commentary_chars} | `{status}` | `{record['commentary_url']}` |")
    lines.extend([
        "",
        "## Records Requiring Human Review",
        "",
        "| Hymn ID | Song No | Missing | Classification | URL |",
        "| --- | --- | --- | --- | --- |",
    ])
    partial_map = {(item.hymn_id, item.song_no): item for item in partials}
    for record in stats["records_requiring_human_review"]:
        item = partial_map.get((record["hymn_id"], record["song_no"]))
        missing = ", ".join(item.missing_fields) if item else "unknown"
        classification = item.classification if item else "UNKNOWN"
        lines.append(f"| `{record['hymn_id']}` | `{record['song_no']}` | {missing} | `{classification}` | `{record['commentary_url']}` |")
    lines.extend([
        "",
        "## Identified Risks",
        "",
        "- Seven records have partial commentary. Automated evidence classifies them as source-missing unless manual inspection proves otherwise.",
        "- Freeze decision should preserve partial records with explicit status rather than fabricating missing commentary.",
        "- Future parser work must use fixtures and a separate repair phase.",
        "",
        "## Freeze Recommendation",
        "",
        f"`{'FREEZE_READY' if freeze_ready else 'REPAIR_REQUIRED'}`",
    ])
    return "\n".join(lines)


def render_freeze_doc(stats: dict, integrity: dict, schema: dict, coverage: dict, partials: list[PartialAudit]) -> str:
    recommendation = "FREEZE_READY" if (
        not schema["schema_violations"]
        and not integrity["duplicate_song_no"]
        and not integrity["duplicate_commentary_urls"]
        and integrity["missing_verse_text"] == 0
        and coverage["average_coverage"] == 1.0
    ) else "REPAIR_REQUIRED"
    return "\n".join([
        "# Corpus Freeze v1 Decision",
        "",
        f"Recommendation: `{recommendation}`",
        "",
        "This document does not freeze the corpus automatically. It records the audit recommendation for `Irandaam Thirumurai Corpus v1`.",
        "",
        "## Justification",
        "",
        f"- Records: `{stats['total_verses']}`",
        f"- Hymns: `{stats['total_hymns']}`",
        f"- Schema violations: `{len(schema['schema_violations'])}`",
        f"- Duplicate `song_no`: `{len(integrity['duplicate_song_no'])}`",
        f"- Missing verse text: `{integrity['missing_verse_text']}`",
        f"- Coverage sample average: `{coverage['average_coverage']:.2%}`",
        f"- Partial commentary records: `{len(partials)}`",
        "",
        "The corpus can be frozen as v1 if the team accepts source-missing commentary sections as known limitations. If full commentary completeness is mandatory, open a separate repair/manual review phase first.",
    ])


def write_manifest(records: list[dict], stats: dict) -> None:
    manifest = {
        "corpus_name": "Irandaam Thirumurai Corpus",
        "version": "candidate-v1",
        "record_count": len(records),
        "hymn_count": stats["total_hymns"],
        "schema_version": "irandaam-thirumurai-jsonl-v0.1",
        "extractor_version": "irandaam_thirumurai_builder:0.1",
        "source": "TamilVU",
        "audit_date": datetime.now(UTC).date().isoformat(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only audit for Irandaam Thirumurai corpus candidate")
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    args = parser.parse_args(argv)
    records = load_records(args.corpus)
    schema = validate_schema(records)
    integrity = integrity_validation(records)
    partials = audit_partials(records)
    coverage = coverage_validation(records)
    stats = corpus_statistics(records)

    write_text(SCHEMA_REPORT, render_schema_report(schema))
    write_text(COVERAGE_REPORT, render_coverage_report(coverage))
    write_text(MANUAL_SAMPLE_REPORT, render_manual_sample(records))
    write_text(AUDIT_REPORT, render_audit_report(records, stats, integrity, schema, coverage, partials))
    write_text(FREEZE_DOC, render_freeze_doc(stats, integrity, schema, coverage, partials))
    write_manifest(records, stats)

    print(f"Audited {len(records)} records")
    print(f"Partial commentary records: {len(partials)}")
    print(f"Schema violations: {len(schema['schema_violations'])}")
    print(f"Coverage sample: {coverage['average_coverage']:.2%}")
    print(f"Main report: {AUDIT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
