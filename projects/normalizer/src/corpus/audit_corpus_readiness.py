from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.normalize_corpus import CORPUS_CONFIGS, load_jsonl, write_json

DEFAULT_INPUT = Path("data/processed/normalized/thirumurai_02_normalized.jsonl")
DEFAULT_CHUNKS = Path("data/processed/chunks/irandaam_thirumurai_chunks.jsonl")
DEFAULT_REGISTRY = Path("data/processed/corpus_registry/thirumurai_registry.json")
DEFAULT_OUTPUT = Path("data/processed/normalized/corpus_readiness_audit.json")
DEFAULT_REPORT = Path("reports/corpus-readiness-audit-report.md")

TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
LETTER_RE = re.compile(r"[A-Za-z\u0B80-\u0BFF]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SYNONYM_TERMS = ("சந்திரன்", "நிலவு", "மதி", "திங்கள்")
FAILURE_CATEGORIES = (
    "data_gap",
    "parser_gap",
    "metadata_gap",
    "citation_gap",
    "retrieval_gap",
    "synonym_gap",
    "aggregation_gap",
    "architecture_gap",
    "llm_gap",
)
FIELD_COVERAGE_FIELDS = (
    "record_id",
    "verse_text",
    "pozhppurai",
    "kurippurai",
    "title",
    "hymn_id",
    "pathigam_id",
    "song_no",
    "author",
    "nayanmar",
    "deity",
    "place",
    "thirumurai_no",
    "source_url",
    "commentary_url",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def coverage(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    present = sum(
        field in record
        and record[field] is not None
        and (not isinstance(record[field], str) or bool(record[field].strip()))
        for record in records
    )
    total = len(records)
    return {
        "present": present,
        "missing": total - present,
        "percentage": round((present / total * 100) if total else 0.0, 2),
    }


def tamil_ratio(text: str) -> float:
    letters = LETTER_RE.findall(text)
    if not letters:
        return 0.0
    return len(TAMIL_RE.findall("".join(letters))) / len(letters)


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def score_from_penalties(*penalties: float) -> int:
    return max(0, min(100, round(100 - sum(penalties))))


def capability(
    name: str,
    readiness: str,
    blocking_issues: list[str],
    recommended_fix: str,
) -> dict[str, Any]:
    return {
        "capability": name,
        "readiness": readiness,
        "blocking_issues": blocking_issues,
        "recommended_fix": recommended_fix,
    }


def audit_records(
    records: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    input_sha256: str = "",
    input_path: str = str(DEFAULT_INPUT),
) -> dict[str, Any]:
    total = len(records)
    field_coverage = {field: coverage(records, field) for field in FIELD_COVERAGE_FIELDS}
    record_ids = Counter(str(record.get("record_id", "")) for record in records)
    duplicate_record_ids = sorted(
        record_id for record_id, count in record_ids.items() if record_id and count > 1
    )
    verse_groups: dict[str, list[str]] = defaultdict(list)
    for record in records:
        verse = str(record.get("verse_text", "")).strip()
        if verse:
            verse_groups[verse].append(str(record.get("record_id", "")))
    duplicate_verse_groups = [
        {"record_ids": sorted(record_ids), "verse_text": verse}
        for verse, record_ids in sorted(verse_groups.items())
        if len(record_ids) > 1
    ]

    verse_lengths = [len(str(record.get("verse_text", ""))) for record in records]
    short_records = [
        record["record_id"] for record in records if 0 < len(record.get("verse_text", "")) < 50
    ]
    long_records = [
        record["record_id"] for record in records if len(record.get("verse_text", "")) > 500
    ]
    malformed_tamil_records = [
        record["record_id"]
        for record in records
        if "\ufffd" in record.get("verse_text", "")
        or CONTROL_RE.search(record.get("verse_text", ""))
    ]
    missing_tamil_records = [
        record["record_id"]
        for record in records
        if record.get("verse_text", "") and not TAMIL_RE.search(record["verse_text"])
    ]
    low_tamil_ratio_records = [
        record["record_id"]
        for record in records
        if record.get("verse_text", "") and tamil_ratio(record["verse_text"]) < 0.75
    ]
    empty_records = sum(not record for record in records)

    field_inconsistencies = 0
    url_identifier_mismatches = 0
    metadata_normalization_problems = 0
    malformed_urls = 0
    traceable_records = 0
    for record in records:
        if record.get("hymn_id") != record.get("pathigam_id"):
            field_inconsistencies += 1
        expected_corpus = (
            f"thirumurai_{record['thirumurai_no']:02d}"
            if isinstance(record.get("thirumurai_no"), int)
            else ""
        )
        if record.get("corpus_id") != expected_corpus:
            field_inconsistencies += 1
        source_url = str(record.get("source_url", ""))
        commentary_url = str(record.get("commentary_url", ""))
        if source_url and not valid_url(source_url):
            malformed_urls += 1
        if commentary_url and not valid_url(commentary_url):
            malformed_urls += 1
        source_params = parse_qs(urlparse(source_url).query)
        commentary_params = parse_qs(urlparse(commentary_url).query)
        source_hymn = (source_params.get("subid") or [""])[0]
        commentary_hymn = (commentary_params.get("sub_id") or [""])[0]
        commentary_song = (commentary_params.get("song_no") or [""])[0]
        if source_hymn and source_hymn != record.get("hymn_id"):
            url_identifier_mismatches += 1
        if commentary_hymn and commentary_hymn != record.get("hymn_id"):
            url_identifier_mismatches += 1
        if commentary_song and commentary_song != record.get("song_no"):
            url_identifier_mismatches += 1
        metadata = record.get("metadata", {})
        if not metadata.get("canonical_id") or not metadata.get("source_record_id"):
            metadata_normalization_problems += 1
        if source_url and metadata.get("source_record_id") and metadata.get("canonical_id"):
            traceable_records += 1

    chunk_counts = Counter(chunk.get("chunk_type", "") for chunk in chunks)
    chunk_parent_ids = {chunk.get("parent_record_id") for chunk in chunks}
    record_id_set = {record.get("record_id") for record in records}
    chunk_types = {
        "verse_only",
        "pozhppurai_only",
        "kurippurai_only",
        "verse_plus_commentary",
        "metadata_context",
    }
    missing_chunk_types = sorted(chunk_types - set(chunk_counts))
    orphan_chunk_parents = sorted(
        parent_id for parent_id in chunk_parent_ids if parent_id not in record_id_set
    )
    records_without_chunks = sorted(record_id_set - chunk_parent_ids)

    synonym_occurrences = {}
    for term in SYNONYM_TERMS:
        verse_records = sum(term in record.get("verse_text", "") for record in records)
        commentary_records = sum(
            term in f"{record.get('pozhppurai', '')} {record.get('kurippurai', '')}"
            for record in records
        )
        synonym_occurrences[term] = {
            "verse_records": verse_records,
            "commentary_records": commentary_records,
        }

    available_corpora = [
        entry["corpus_id"]
        for entry in registry.get("corpora", [])
        if entry.get("status") == "available"
    ]
    annotations = {
        "deity_names": all(bool(record.get("deity")) for record in records),
        "epithets": any("epithets" in record.get("metadata", {}) for record in records),
        "similes": any("similes" in record.get("metadata", {}) for record in records),
        "metaphors": any("metaphors" in record.get("metadata", {}) for record in records),
        "natural_imagery": any(
            "natural_imagery" in record.get("metadata", {}) for record in records
        ),
        "literary_motifs": any(
            "motifs" in record.get("metadata", {}) for record in records
        ),
        "synonym_concepts": any(
            "synonym_concepts" in record.get("metadata", {}) for record in records
        ),
    }

    issue_counts = {
        "empty_records": empty_records,
        "duplicate_record_ids": len(duplicate_record_ids),
        "duplicate_verse_text_groups": len(duplicate_verse_groups),
        "unusually_short_verses": len(short_records),
        "unusually_long_verses": len(long_records),
        "malformed_tamil_text": len(malformed_tamil_records),
        "missing_tamil_text": len(missing_tamil_records),
        "low_tamil_ratio": len(low_tamil_ratio_records),
        "missing_verse_text": field_coverage["verse_text"]["missing"],
        "missing_pozhppurai": field_coverage["pozhppurai"]["missing"],
        "missing_kurippurai": field_coverage["kurippurai"]["missing"],
        "missing_title": field_coverage["title"]["missing"],
        "missing_hymn_id": field_coverage["hymn_id"]["missing"],
        "missing_song_no": field_coverage["song_no"]["missing"],
        "field_inconsistencies": field_inconsistencies,
        "missing_author": field_coverage["author"]["missing"],
        "missing_nayanmar": field_coverage["nayanmar"]["missing"],
        "missing_deity": field_coverage["deity"]["missing"],
        "missing_place": field_coverage["place"]["missing"],
        "missing_thirumurai_no": field_coverage["thirumurai_no"]["missing"],
        "metadata_normalization_problems": metadata_normalization_problems,
        "missing_source_url": field_coverage["source_url"]["missing"],
        "missing_commentary_url": field_coverage["commentary_url"]["missing"],
        "malformed_urls": malformed_urls,
        "missing_citation_text": sum(
            not record.get("metadata", {}).get("citation_text") for record in records
        ),
        "url_identifier_mismatches": url_identifier_mismatches,
        "orphan_chunk_parents": len(orphan_chunk_parents),
        "records_without_chunks": len(records_without_chunks),
    }

    data_quality_score = score_from_penalties(
        empty_records * 10,
        len(duplicate_record_ids) * 5,
        len(duplicate_verse_groups) * 1,
        len(short_records) * 0.25,
        len(long_records) * 0.25,
        len(malformed_tamil_records) * 5,
        len(missing_tamil_records) * 5,
    )
    parser_readiness_score = score_from_penalties(
        field_coverage["verse_text"]["missing"] * 5,
        field_coverage["title"]["missing"] * 2,
        field_coverage["hymn_id"]["missing"] * 3,
        field_coverage["song_no"]["missing"] * 3,
        field_inconsistencies * 2,
        (field_coverage["pozhppurai"]["missing"] + field_coverage["kurippurai"]["missing"])
        / max(total, 1)
        * 20,
    )
    metadata_readiness_score = score_from_penalties(
        (
            field_coverage["author"]["missing"]
            + field_coverage["nayanmar"]["missing"]
            + field_coverage["place"]["missing"]
            + field_coverage["thirumurai_no"]["missing"]
        )
        / max(total, 1)
        * 50,
        metadata_normalization_problems / max(total, 1) * 20,
        10 if not annotations["epithets"] else 0,
        5 if len(available_corpora) < 2 else 0,
    )
    citation_readiness_score = score_from_penalties(
        (
            issue_counts["missing_source_url"]
            + issue_counts["missing_commentary_url"]
            + issue_counts["missing_citation_text"]
        )
        / max(total, 1)
        * 50,
        malformed_urls * 2,
        url_identifier_mismatches * 2,
        (total - traceable_records) / max(total, 1) * 20,
    )
    retrieval_readiness_score = score_from_penalties(
        len(missing_chunk_types) * 10,
        len(orphan_chunk_parents) * 2,
        len(records_without_chunks) * 2,
        5 if chunk_counts.get("verse_plus_commentary", 0) != total else 0,
    )
    analytical_readiness_score = score_from_penalties(
        10 if not annotations["synonym_concepts"] else 0,
        10 if not annotations["epithets"] else 0,
        10 if not annotations["similes"] else 0,
        10 if not annotations["metaphors"] else 0,
        10 if not annotations["natural_imagery"] else 0,
        10 if not annotations["literary_motifs"] else 0,
        15 if len(available_corpora) < 2 else 0,
        10,  # No explicit exhaustive aggregation execution layer yet.
    )
    scaling_readiness_score = score_from_penalties(
        15 if len(available_corpora) < 2 else 0,
        10,  # Only the SLET/Tevaram parser family is proven.
        10,  # Multi-author and non-pathigam structures are unproven.
        5 if not annotations["epithets"] else 0,
    )
    scores = {
        "data_quality_score": data_quality_score,
        "parser_readiness_score": parser_readiness_score,
        "metadata_readiness_score": metadata_readiness_score,
        "citation_readiness_score": citation_readiness_score,
        "retrieval_readiness_score": retrieval_readiness_score,
        "analytical_readiness_score": analytical_readiness_score,
        "scaling_readiness_score": scaling_readiness_score,
    }
    scores["overall_readiness_score"] = round(mean(scores.values()))

    retrieval_ready = chunk_counts.get("verse_plus_commentary", 0) == total and total > 0
    multi_corpus_available = len(available_corpora) >= 2
    capabilities = [
        capability(
            "ordinary RAG",
            "ready" if retrieval_ready else "not_ready",
            [] if retrieval_ready else ["No corpus-specific chunks or retrieval index exist."],
            "Keep hybrid retrieval and citation validation as the default path."
            if retrieval_ready
            else "Create and benchmark pilot-specific retrieval artifacts in a separate approved phase.",
        ),
        capability(
            "verse lookup",
            "ready" if chunk_counts.get("verse_only", 0) == total and total > 0 else "partial",
            [] if chunk_counts.get("verse_only", 0) == total and total > 0 else ["Normalized verse text exists, but verse-only chunks do not."],
            "Retain exact Tamil text and add deterministic verse-only chunks.",
        ),
        capability("author lookup", "ready", [], "Preserve normalized and original author labels."),
        capability("hymn identification", "ready", [], "Keep hymn, pathigam, song, and source URL identifiers aligned."),
        capability(
            "word occurrence search",
            "partial",
            ["No dedicated exhaustive aggregation command or morphology handling."],
            "Add a deterministic field-aware occurrence and count layer.",
        ),
        capability(
            "synonym expansion",
            "not_ready",
            ["No versioned Tamil literary synonym lexicon or concept IDs."],
            "Create a curated synonym authority with source forms and review metadata.",
        ),
        capability(
            "deity/epithet analysis",
            "not_ready",
            ["Deity is corpus-level normalized; epithets are not extracted or linked."],
            "Add reviewed deity aliases, epithet spans, entity IDs, and evidence offsets.",
        ),
        capability(
            "simile/metaphor analysis",
            "not_ready",
            ["No simile or metaphor annotations exist."],
            "Design a versioned literary-device annotation schema and human-reviewed sample.",
        ),
        capability(
            "Nayanmar comparison",
            "partial" if multi_corpus_available else "not_ready",
            ["The Appar corpus is a five-hymn pilot, not complete coverage."]
            if multi_corpus_available
            else ["Only one available Nayanmar corpus is normalized."],
            "Complete and audit comparable author corpora before quantitative comparison.",
        ),
        capability(
            "cross-corpus comparison",
            "partial" if multi_corpus_available else "not_ready",
            ["The second corpus is pilot-sized and cannot support exhaustive claims."]
            if multi_corpus_available
            else ["Only thirumurai_02 is available."],
            "Pilot each new corpus family and normalize shared author, place, work, and deity metadata.",
        ),
        capability(
            "corpus-wide aggregation",
            "partial",
            ["The data is scan-ready but no dedicated aggregation result contract exists."],
            "Add deterministic group/count/list operations with complete evidence and citations.",
        ),
        capability(
            "failure diagnosis",
            "partial",
            ["Failure categories exist, but later analysis and LLM stages are not instrumented."],
            "Carry failure attribution and evidence through every future pipeline stage.",
        ),
    ]

    scaling_risks = [
        {
            "risk": "parser_family_variation",
            "severity": "high",
            "detail": "The proven parser targets SLET Tevaram hymn/commentary pages; Thirumurai 8-12 may use different work and section structures.",
        },
        {
            "risk": "multi_author_attribution",
            "severity": "high",
            "detail": "Thirumurai 9 and 11 require record-level author attribution rather than one corpus-level author.",
        },
        {
            "risk": "identifier_collision",
            "severity": "medium",
            "detail": "Source song and hymn numbers must remain namespaced by corpus and work.",
        },
        {
            "risk": "metadata_false_uniformity",
            "severity": "high",
            "detail": "Pathigam, place, deity, and commentary assumptions cannot be forced onto structurally different works.",
        },
        {
            "risk": "analytical_claim_overreach",
            "severity": "high",
            "detail": "Top-k retrieval cannot support claims such as all, most, or compare across the corpus.",
        },
        {
            "risk": "annotation_absence",
            "severity": "high",
            "detail": "Synonyms, epithets, imagery, motifs, similes, and metaphors are not yet normalized.",
        },
    ]
    recommendations = [
        "Inspect and pilot one additional Tevaram corpus before broadening to a structurally different Thirumurai.",
        "Create source-family adapters that emit the unified schema without assuming every work is a Tevaram pathigam.",
        "Build deterministic corpus-wide occurrence and aggregation operations before analytical answer generation.",
        "Design a versioned Tamil literary synonym lexicon with concept IDs, variants, citations, and reviewer metadata.",
        "Add evidence-bearing entity, epithet, imagery, motif, simile, and metaphor annotation contracts.",
        "Require source inspection, parser sampling, normalization validation, and corpus audit for every new registry entry.",
    ]

    return {
        "audit_version": "corpus-readiness-audit-v1",
        "input": {
            "path": input_path,
            "sha256": input_sha256,
        },
        "summary": {
            "record_count": total,
            "unique_hymns": len({record.get("hymn_id") for record in records}),
            "available_corpora": available_corpora,
            "chunk_count": len(chunks),
            "overall_status": (
                "READY_FOR_CONTROLLED_PILOT_EXPANSION"
                if scores["scaling_readiness_score"] >= 60
                else "REMEDIATION_REQUIRED_BEFORE_SCALING"
            ),
        },
        "scores": scores,
        "field_coverage": field_coverage,
        "issue_counts": issue_counts,
        "data_quality": {
            "verse_length": {
                "minimum": min(verse_lengths) if verse_lengths else 0,
                "maximum": max(verse_lengths) if verse_lengths else 0,
                "average": round(mean(verse_lengths), 2) if verse_lengths else 0.0,
            },
            "duplicate_record_ids": duplicate_record_ids,
            "duplicate_verse_text_groups": duplicate_verse_groups,
            "unusually_short_record_ids": short_records,
            "unusually_long_record_ids": long_records,
            "malformed_tamil_record_ids": malformed_tamil_records,
            "missing_tamil_record_ids": missing_tamil_records,
            "low_tamil_ratio_record_ids": low_tamil_ratio_records,
        },
        "parser_readiness": {
            "field_consistency_issues": field_inconsistencies,
            "commentary_source_missing_records": (
                field_coverage["pozhppurai"]["missing"]
                + field_coverage["kurippurai"]["missing"]
            ),
            "note": "Known empty commentary fields were previously audited as source-missing, not parser bugs.",
        },
        "metadata_readiness": {
            "normalization_problems": metadata_normalization_problems,
            "annotations_present": annotations,
        },
        "citation_readiness": {
            "traceable_records": traceable_records,
            "traceability_percentage": round(
                traceable_records / total * 100 if total else 0.0, 2
            ),
            "url_identifier_mismatches": url_identifier_mismatches,
        },
        "retrieval_readiness": {
            "chunk_types": dict(sorted(chunk_counts.items())),
            "missing_chunk_types": missing_chunk_types,
            "orphan_chunk_parents": orphan_chunk_parents,
            "records_without_chunks": records_without_chunks,
            "verse_only_supported": chunk_counts.get("verse_only", 0) == total,
            "commentary_retrieval_supported": bool(
                chunk_counts.get("pozhppurai_only")
                and chunk_counts.get("kurippurai_only")
            ),
            "metadata_retrieval_supported": chunk_counts.get("metadata_context", 0) == total,
            "analytical_chunking_note": "Current chunks support retrieval, not exhaustive corpus analysis.",
        },
        "analytical_readiness": {
            "capabilities": capabilities,
            "synonym_term_occurrences": synonym_occurrences,
            "motif_entity_annotations": annotations,
        },
        "scaling_risks": scaling_risks,
        "failure_attribution_categories": list(FAILURE_CATEGORIES),
        "recommendations": recommendations,
    }


def percentage_row(field: str, details: dict[str, Any]) -> str:
    return (
        f"| `{field}` | {details['present']} | {details['missing']} | "
        f"{details['percentage']:.2f}% |"
    )


def render_report(audit: dict[str, Any]) -> str:
    scores = audit["scores"]
    score_rows = "\n".join(
        f"| {name.replace('_', ' ').title()} | {value} |"
        for name, value in scores.items()
    )
    coverage_rows = "\n".join(
        percentage_row(field, details)
        for field, details in audit["field_coverage"].items()
    )
    capability_rows = "\n".join(
        "| {capability} | {readiness} | {issues} | {fix} |".format(
            capability=item["capability"],
            readiness=item["readiness"],
            issues="; ".join(item["blocking_issues"]) or "None",
            fix=item["recommended_fix"],
        )
        for item in audit["analytical_readiness"]["capabilities"]
    )
    synonym_rows = "\n".join(
        f"| `{term}` | {counts['verse_records']} | {counts['commentary_records']} |"
        for term, counts in audit["analytical_readiness"]["synonym_term_occurrences"].items()
    )
    risks = "\n".join(
        f"- **{item['severity'].upper()} - {item['risk']}:** {item['detail']}"
        for item in audit["scaling_risks"]
    )
    recommendations = "\n".join(
        f"{index}. {recommendation}"
        for index, recommendation in enumerate(audit["recommendations"], start=1)
    )
    duplicate_groups = audit["data_quality"]["duplicate_verse_text_groups"]
    duplicate_rows = "\n".join(
        f"| {index} | {', '.join(f'`{record_id}`' for record_id in group['record_ids'])} |"
        for index, group in enumerate(duplicate_groups, start=1)
    ) or "| None | None |"
    issues = audit["issue_counts"]
    retrieval = audit["retrieval_readiness"]
    comparison = audit.get("comparison_with_thirumurai_02")
    comparison_section = ""
    if comparison:
        base = comparison["thirumurai_02_scores"]
        pilot = comparison["pilot_scores"]
        commentary = comparison["commentary_coverage"]
        comparison_section = f"""
## Comparison With Thirumurai 02

| Measure | Thirumurai 02 | Pilot |
| --- | ---: | ---: |
| Overall readiness | {base["overall_readiness_score"]} | {pilot["overall_readiness_score"]} |
| Parser readiness | {base["parser_readiness_score"]} | {pilot["parser_readiness_score"]} |
| Metadata readiness | {base["metadata_readiness_score"]} | {pilot["metadata_readiness_score"]} |
| Citation readiness | {base["citation_readiness_score"]} | {pilot["citation_readiness_score"]} |
| Retrieval readiness | {base["retrieval_readiness_score"]} | {pilot["retrieval_readiness_score"]} |
| Pozhppurai coverage | {commentary["thirumurai_02_pozhppurai"]:.2f}% | {commentary["pilot_pozhppurai"]:.2f}% |
| Kurippurai coverage | {commentary["thirumurai_02_kurippurai"]:.2f}% | {commentary["pilot_kurippurai"]:.2f}% |

The pilot parser is source-family specific. Its richer commentary labels and hymn-local song numbering must remain explicit rather than being forced through the Second Thirumurai assumptions.
"""
    corpus_label = audit["input"]["path"]
    source_omission_count = issues["missing_pozhppurai"] + issues["missing_kurippurai"]
    return f"""# Corpus Readiness Audit Report

## Executive Summary

- Records audited: `{audit["summary"]["record_count"]}`
- Unique hymns: `{audit["summary"]["unique_hymns"]}`
- Available corpora: `{", ".join(audit["summary"]["available_corpora"])}`
- Retrieval chunks inspected: `{audit["summary"]["chunk_count"]}`
- Overall readiness score: `{scores["overall_readiness_score"]}/100`
- Scaling decision: `{audit["summary"]["overall_status"]}`

This audit covers `{corpus_label}`. Structural extraction is strong, but broad multi-Thirumurai analytical claims remain blocked by incomplete cross-corpus coverage, no synonym authority, no literary-entity annotations, and no exhaustive aggregation layer.

## Readiness Scores

| Area | Score |
| --- | ---: |
{score_rows}

## Field Coverage

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
{coverage_rows}

## Data And Parser Risks

- Empty records: `{issues["empty_records"]}`
- Duplicate record IDs: `{issues["duplicate_record_ids"]}`
- Duplicate verse-text groups: `{issues["duplicate_verse_text_groups"]}`
- Unusually short verses: `{issues["unusually_short_verses"]}`
- Unusually long verses: `{issues["unusually_long_verses"]}`
- Malformed Tamil text: `{issues["malformed_tamil_text"]}`
- Missing Tamil text: `{issues["missing_tamil_text"]}`
- Missing pozhppurai: `{issues["missing_pozhppurai"]}`
- Missing kurippurai: `{issues["missing_kurippurai"]}`
- Field consistency issues: `{issues["field_inconsistencies"]}`

Empty commentary field count across both commentary columns: `{source_omission_count}`. Source and parser evidence must be reviewed before assigning blame; the pilot's known missing pair is caused by a TamilVU endpoint null-pointer response.

### Duplicate Verse Review

| Group | Record IDs |
| ---: | --- |
{duplicate_rows}

These exact-text groups require source-aware human review. Repeated devotional refrains can be legitimate, so the audit does not automatically classify them as parser corruption.

## Citation And Source Readiness

- Traceable records: `{audit["citation_readiness"]["traceable_records"]}` (`{audit["citation_readiness"]["traceability_percentage"]:.2f}%`)
- Missing source URLs: `{issues["missing_source_url"]}`
- Missing commentary URLs: `{issues["missing_commentary_url"]}`
- Missing citation text: `{issues["missing_citation_text"]}`
- Malformed URLs: `{issues["malformed_urls"]}`
- URL identifier mismatches: `{issues["url_identifier_mismatches"]}`

## Retrieval And Chunking

- Verse-only retrieval supported: `{retrieval["verse_only_supported"]}`
- Commentary retrieval supported: `{retrieval["commentary_retrieval_supported"]}`
- Metadata retrieval supported: `{retrieval["metadata_retrieval_supported"]}`
- Missing chunk types: `{retrieval["missing_chunk_types"] or "none"}`
- Records without chunks: `{len(retrieval["records_without_chunks"])}`

Current chunk readiness is reported exactly as observed. Even when chunks exist, they support passage retrieval and citation rather than exhaustive corpus analysis.

## Capability Readiness

| Capability | Readiness | Blocking Issues | Recommended Fix |
| --- | --- | --- | --- |
{capability_rows}

## Synonym Readiness

Exact surface-form evidence exists, but the forms are not linked under a shared literary concept.

| Term | Verse Records | Commentary Records |
| --- | ---: | ---: |
{synonym_rows}

A versioned Tamil literary synonym lexicon is required before combining these forms in a complete, auditable result.

## Motif And Entity Readiness

The normalized corpus carries a corpus-level deity value, but does not yet contain evidence spans or authority records for epithets, similes, metaphors, natural imagery, or repeated motifs. These capabilities are not ready for automated literary claims.

## Scaling Risks

{risks}

## Failure Attribution

Future failures should be attributed to: `{", ".join(audit["failure_attribution_categories"])}`.

This separates missing source data from parser, metadata, citation, retrieval, synonym, aggregation, architecture, and future LLM failures.

## Recommendations

{recommendations}

{comparison_section}
"""


def write_outputs(audit: dict[str, Any], output: Path, report: Path) -> None:
    write_json(output, audit)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(audit), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit corpus, parser, retrieval, and analytical readiness."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--corpus-id", choices=sorted(CORPUS_CONFIGS), default="thirumurai_02")
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    config = CORPUS_CONFIGS[args.corpus_id]
    input_path = args.input if args.input != DEFAULT_INPUT or args.corpus_id == "thirumurai_02" else config["output"]
    chunks_path = args.chunks
    if args.corpus_id != "thirumurai_02" and args.chunks == DEFAULT_CHUNKS:
        chunks_path = Path("data/processed/chunks") / f"{args.corpus_id}_chunks.jsonl"
    output_path = (
        Path("data/processed/normalized") / f"{args.corpus_id}_readiness_audit.json"
        if args.corpus_id != "thirumurai_02" and args.output == DEFAULT_OUTPUT
        else args.output
    )
    report_path = (
        Path("reports/pilot-corpus-readiness-report.md")
        if args.corpus_id != "thirumurai_02" and args.report == DEFAULT_REPORT
        else args.report
    )
    before_hash = sha256(input_path)
    records = load_jsonl(input_path)
    chunks = load_jsonl(chunks_path) if chunks_path.exists() else []
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    audit = audit_records(
        records,
        chunks,
        registry,
        input_sha256=before_hash,
        input_path=str(input_path),
    )
    if args.corpus_id != "thirumurai_02":
        existing_path = Path("data/processed/normalized/corpus_readiness_audit.json")
        if existing_path.exists():
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            audit["comparison_with_thirumurai_02"] = {
                "thirumurai_02_scores": existing["scores"],
                "pilot_scores": audit["scores"],
                "parser_difference": audit["scores"]["parser_readiness_score"]
                - existing["scores"]["parser_readiness_score"],
                "metadata_difference": audit["scores"]["metadata_readiness_score"]
                - existing["scores"]["metadata_readiness_score"],
                "citation_difference": audit["scores"]["citation_readiness_score"]
                - existing["scores"]["citation_readiness_score"],
                "commentary_coverage": {
                    "thirumurai_02_pozhppurai": existing["field_coverage"]["pozhppurai"]["percentage"],
                    "pilot_pozhppurai": audit["field_coverage"]["pozhppurai"]["percentage"],
                    "thirumurai_02_kurippurai": existing["field_coverage"]["kurippurai"]["percentage"],
                    "pilot_kurippurai": audit["field_coverage"]["kurippurai"]["percentage"],
                },
            }
    write_outputs(audit, output_path, report_path)
    after_hash = sha256(input_path)
    if before_hash != after_hash:
        raise RuntimeError("normalized corpus changed during read-only audit")

    print(f"Records audited: {audit['summary']['record_count']}")
    print(f"Overall readiness: {audit['scores']['overall_readiness_score']}")
    print(f"Parser readiness: {audit['scores']['parser_readiness_score']}")
    print(f"Analytical readiness: {audit['scores']['analytical_readiness_score']}")
    print(f"Scaling status: {audit['summary']['overall_status']}")
    print(f"Corpus: {args.corpus_id}")
    print(f"JSON: {output_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
