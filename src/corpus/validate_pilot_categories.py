from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.pilot_ingest_category import load_json, load_jsonl
from corpus.normalize_category_corpus import normalize_record
from corpus.validate_category_corpus import REQUIRED_FIELDS, validate_records
from parsers.base_parser import ParseContext
from parsers.dictionary_parser import DictionaryParser
from parsers.grammar_parser import GrammarParser
from parsers.prose_parser import ProseParser
from parsers.verse_parser import VerseParser

DEFAULT_PLAN = Path("data/processed/corpus_registry/pilot_category_plan.json")
DEFAULT_OUTPUT = Path(
    "data/processed/pilot_categories/pilot_category_validation_summary.json"
)
DEFAULT_REPORT = Path("reports/pilot-category-validation-report.md")
VERIFIED_STATUSES = {"local_seed_ready", "verified", "pilot_verified"}

OPTIONAL_FIELDS = {
    "saivam": (
        "author",
        "corpus_id",
        "hymn_id",
        "pathigam_id",
        "song_no",
        "verse_no",
        "pozhppurai",
        "kurippurai",
        "commentary_url",
    ),
    "dictionaries": (
        "entry_headword",
        "definition",
        "part_of_speech",
        "collection_id",
        "period",
    ),
    "sangam_literature": (
        "author",
        "poem_no",
        "verse_no",
        "song_no",
        "thinai",
        "thurai",
        "colophon",
        "commentary_url",
    ),
    "grammar": (
        "author",
        "rule_no",
        "rule_text",
        "explanation_text",
        "section_id",
        "chapter_id",
        "commentary_url",
    ),
    "twentieth_century_prose": (
        "author",
        "title",
        "chapter_id",
        "section_id",
        "period",
        "genre",
    ),
}


def verified_pilots(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        pilot
        for pilot in plan.get("pilots", [])
        if pilot.get("status") in VERIFIED_STATUSES
    ]


def coverage(records: list[dict[str, Any]], fields: tuple[str, ...] | list[str]) -> float:
    if not records or not fields:
        return 0.0
    present = sum(
        bool(str(record.get(field) or "").strip())
        for record in records
        for field in fields
    )
    return round(present / (len(records) * len(fields)), 4)


def record_types(records: list[dict[str, Any]]) -> list[str]:
    return sorted({str(record.get("record_type") or "") for record in records if record.get("record_type")})


def citation_readiness(category_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    source_ready = coverage(records, ["source_url"])
    if category_id == "saivam":
        identity_fields = ["book_id", "work_id", "hymn_id", "song_no"]
    elif category_id == "sangam_literature":
        identity_fields = ["book_id", "work_id", "poem_no"]
    elif category_id == "grammar":
        identity_fields = ["book_id", "work_id", "rule_no"]
    elif category_id == "twentieth_century_prose":
        identity_fields = ["book_id", "work_id", "section_id"]
    else:
        identity_fields = ["book_id", "work_id", "entry_headword"]
    identity_ready = coverage(records, identity_fields)
    citation_text_coverage = (
        round(
            sum(
                bool(str(record.get("source_metadata", {}).get("citation_text") or "").strip())
                for record in records
            )
            / len(records),
            4,
        )
        if records
        else 0.0
    )
    status = (
        "READY"
        if source_ready == 1.0 and identity_ready == 1.0
        else "PARTIAL"
    )
    return {
        "status": status,
        "source_url_coverage": source_ready,
        "identity_coverage": identity_ready,
        "citation_text_coverage": citation_text_coverage,
    }


def analytical_usefulness(category_id: str) -> dict[str, Any]:
    if category_id == "saivam":
        return {
            "score": 95,
            "uses": [
                "verse lookup",
                "commentary comparison",
                "deity and devotional motif analysis",
                "poetic language study",
            ],
        }
    if category_id == "sangam_literature":
        return {
            "score": 96,
            "uses": [
                "anthology and poem lookup",
                "poet comparison",
                "thinai and situation analysis",
                "classical poetic language comparison",
            ],
        }
    if category_id == "grammar":
        return {
            "score": 88,
            "uses": [
                "grammar rule lookup",
                "rule-to-literary-usage comparison",
                "linguistic classification",
                "future example and exception analysis",
            ],
        }
    if category_id == "twentieth_century_prose":
        return {
            "score": 92,
            "uses": [
                "paragraph and section lookup",
                "author style comparison",
                "theme and motif analysis",
                "cross-genre literary comparison",
            ],
        }
    return {
        "score": 78,
        "uses": [
            "headword explanation",
            "future synonym authority",
            "rare-word support",
            "lexical comparison with literary usage",
        ],
    }


def load_verified_records(
    pilot: dict[str, Any], base_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    category_id = pilot["category_id"]
    if category_id == "saivam":
        source = (
            base_dir / "data/processed/normalized/thirumurai_04_normalized.jsonl"
        )
        source_records = load_jsonl(source, 10)
        from parsers.base_parser import parser_for_family

        context = ParseContext(
            category_id="saivam",
            category_tamil=pilot["category_tamil"],
            parser_family=pilot["parser_family"],
            book_id=pilot["book_id"],
            work_id=pilot["work_id"],
            pilot_id=pilot["pilot_id"],
        )
        parsed = [
            record
            for source_record in source_records
            for record in parser_for_family("verse_parser").parse(source_record, context)
        ]
        return parsed, [normalize_record(record) for record in parsed], str(
            source.relative_to(base_dir)
        )
    if category_id == "dictionaries":
        metadata_path = base_dir / pilot["source_path"]
        metadata = load_json(metadata_path)
        entry = next(
            item
            for item in metadata["fixtures"]
            if item["page_type"] == "dictionary_entry"
        )
        context = ParseContext(
            category_id="dictionaries",
            category_tamil=pilot["category_tamil"],
            parser_family=pilot["parser_family"],
            book_id=pilot["book_id"],
            work_id=pilot["work_id"],
            pilot_id=pilot["pilot_id"],
        )
        source = {
            **entry,
            "source_work": metadata["source_work"],
            "html_content": (base_dir / entry["fixture_path"]).read_text(encoding="utf-8"),
        }
        parsed = DictionaryParser().parse(source, context)
        return parsed, [normalize_record(record) for record in parsed], str(
            metadata_path.relative_to(base_dir)
        )
    if category_id == "sangam_literature":
        metadata_path = base_dir / pilot["source_path"]
        metadata = load_json(metadata_path)
        poem_fixture = next(
            item for item in metadata["fixtures"] if item["page_type"] == "poem_group"
        )
        context = ParseContext(
            category_id=category_id,
            category_tamil=pilot["category_tamil"],
            parser_family=pilot["parser_family"],
            book_id=pilot["book_id"],
            work_id=pilot["work_id"],
            pilot_id=pilot["pilot_id"],
        )
        source = {
            **poem_fixture,
            "source_work": metadata["source_work"],
            "html_content": (base_dir / poem_fixture["fixture_path"]).read_text(
                encoding="utf-8"
            ),
        }
        parsed = VerseParser().parse(source, context)
        return parsed, [normalize_record(record) for record in parsed], str(
            metadata_path.relative_to(base_dir)
        )
    if category_id == "grammar":
        metadata_path = base_dir / pilot["source_path"]
        metadata = load_json(metadata_path)
        rule_fixture = next(
            item for item in metadata["fixtures"] if item["page_type"] == "grammar_rules"
        )
        context = ParseContext(
            category_id=category_id,
            category_tamil=pilot["category_tamil"],
            parser_family=pilot["parser_family"],
            book_id=pilot["book_id"],
            work_id=pilot["work_id"],
            pilot_id=pilot["pilot_id"],
        )
        source = {
            **rule_fixture,
            "source_work": metadata["source_work"],
            "html_content": (base_dir / rule_fixture["fixture_path"]).read_text(
                encoding="utf-8"
            ),
        }
        parsed = GrammarParser().parse(source, context)
        return parsed, [normalize_record(record) for record in parsed], str(
            metadata_path.relative_to(base_dir)
        )
    if category_id == "twentieth_century_prose":
        metadata_path = base_dir / pilot["source_path"]
        metadata = load_json(metadata_path)
        prose_fixture = next(
            item for item in metadata["fixtures"] if item["page_type"] == "prose_section"
        )
        context = ParseContext(
            category_id=category_id,
            category_tamil=pilot["category_tamil"],
            parser_family=pilot["parser_family"],
            book_id=pilot["book_id"],
            work_id=pilot["work_id"],
            pilot_id=pilot["pilot_id"],
        )
        source = {
            **prose_fixture,
            "source_work": metadata["source_work"],
            "html_content": (base_dir / prose_fixture["fixture_path"]).read_text(
                encoding="utf-8"
            ),
        }
        parsed = ProseParser().parse(source, context)
        return parsed, [normalize_record(record) for record in parsed], str(
            metadata_path.relative_to(base_dir)
        )
    raise ValueError(f"unsupported verified pilot category: {category_id}")


def compare_pilot(
    pilot: dict[str, Any], base_dir: Path
) -> dict[str, Any]:
    category_id = pilot["category_id"]
    processed, normalized, evidence_path = load_verified_records(pilot, base_dir)
    validation = validate_records(normalized, category_id)
    required_coverage = coverage(normalized, list(REQUIRED_FIELDS))
    optional_coverage = coverage(normalized, list(OPTIONAL_FIELDS.get(category_id, ())))
    commentary_applicable = category_id in {
        "saivam",
        "sangam_literature",
        "grammar",
    }
    commentary_url_coverage = (
        coverage(normalized, ["commentary_url"]) if commentary_applicable else None
    )
    metadata_fields = (
        ["parser_family", "pilot_id", "pilot_scope", "source_record_id"]
        if category_id == "saivam"
        else [
            "parser_family",
            "pilot_id",
            "pilot_scope",
            "source_record_id",
            "fixture_path",
            "original_sha256",
            "source_work",
        ]
    )
    metadata_coverage = (
        round(
            sum(
                bool(str(record.get("source_metadata", {}).get(field) or "").strip())
                for record in normalized
                for field in metadata_fields
            )
            / (len(normalized) * len(metadata_fields)),
            4,
        )
        if normalized
        else 0.0
    )
    citation = citation_readiness(category_id, normalized)
    usefulness = analytical_usefulness(category_id)
    readiness_score = round(
        (
            required_coverage * 30
            + validation["source_url_coverage"] * 20
            + metadata_coverage * 20
            + (1 if validation["status"] == "VALID" else 0) * 20
            + (usefulness["score"] / 100) * 10
        ),
        1,
    )
    return {
        "category_id": category_id,
        "category_tamil": pilot["category_tamil"],
        "parser_family": pilot["parser_family"],
        "record_types": record_types(normalized),
        "records_parsed": len(processed),
        "records_normalized": len(normalized),
        "manifest_record_count": pilot.get("verified_record_count", len(processed)),
        "validation_status": validation["status"],
        "validation_errors": validation["error_count"],
        "required_field_coverage": required_coverage,
        "optional_field_coverage": optional_coverage,
        "source_url_coverage": validation["source_url_coverage"],
        "commentary_url_coverage": commentary_url_coverage,
        "citation_readiness": citation,
        "metadata_completeness": metadata_coverage,
        "analytical_usefulness": usefulness,
        "readiness_score": readiness_score,
        "evidence_path": evidence_path,
    }


def schema_stress_test(comparisons: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_category = {item["category_id"]: item for item in comparisons}
    verse = by_category.get("saivam")
    sangam = by_category.get("sangam_literature")
    dictionary = by_category.get("dictionaries")
    grammar = by_category.get("grammar")
    prose = by_category.get("twentieth_century_prose")
    return [
        {
            "schema_area": "verse_records",
            "status": (
                "supported"
                if verse
                and verse["validation_errors"] == 0
                and sangam
                and sangam["validation_errors"] == 0
                else "partial"
            ),
            "evidence": (
                f"{verse['records_normalized']} devotional and "
                f"{sangam['records_normalized']} Sangam verse records retain their distinct "
                "hierarchies, authorship, literary metadata, and source identity."
                if verse and sangam
                else "No verified verse pilot was available."
            ),
            "recommended_change": (
                "Keep hymn and anthology metadata optional and type-specific within the common envelope."
            ),
        },
        {
            "schema_area": "commentary_records",
            "status": "partial",
            "evidence": (
                "Pozhppurai and kurippurai are preserved on verse records with commentary URLs, "
                "but commentary is not represented as an independent record type."
            ),
            "recommended_change": (
                "Define a standalone commentary record/link contract before cross-work commentary analysis."
            ),
        },
        {
            "schema_area": "dictionary_entries",
            "status": (
                "supported"
                if dictionary and dictionary["validation_errors"] == 0
                else "not_supported"
            ),
            "evidence": (
                f"{dictionary['records_normalized']} normalized entry retains headword, definition, "
                "source URL, deterministic ID, and fixture provenance."
                if dictionary
                else "No verified dictionary pilot was available."
            ),
            "recommended_change": (
                "Add ordered sense, example, etymology, and cross-reference structures only after varied fixtures."
            ),
        },
        {
            "schema_area": "grammar_rules",
            "status": (
                "supported"
                if grammar and grammar["validation_errors"] == 0
                else "not_supported"
            ),
            "evidence": (
                f"{grammar['records_normalized']} normalized grammar rules retain rule "
                "number, rule text, chapter, section, commentary URL, and provenance."
                if grammar
                else "No verified grammar pilot was available."
            ),
            "recommended_change": (
                "Add structured examples, exceptions, commentator identity, and cross-rule links after varied fixtures."
            ),
        },
        {
            "schema_area": "prose_sections",
            "status": (
                "supported"
                if prose and prose["validation_errors"] == 0
                else "not_supported"
            ),
            "evidence": (
                f"{prose['records_normalized']} normalized prose paragraphs retain "
                "work, chapter, section, title, author, source URL, and rights metadata."
                if prose
                else "No verified prose pilot was available."
            ),
            "recommended_change": (
                "Add page, footnote, quotation, and edition structures after permissioned source fixtures."
            ),
        },
    ]


def next_pilot_recommendation(plan: dict[str, Any]) -> dict[str, Any]:
    pending = {
        pilot["category_id"]: pilot
        for pilot in plan.get("pilots", [])
        if pilot.get("status") not in VERIFIED_STATUSES
    }
    if "twentieth_century_prose" in pending:
        return {
            "category_id": "twentieth_century_prose",
            "parser_family": "prose_parser",
            "reason": (
                "Prose is the next distinct typed-text hierarchy after grammar, while "
                "encyclopedia content remains a higher-risk mixed article/media shape."
            ),
            "risk": "high",
            "next_action": "complete rights review, then collect exactly three allowlisted prose fixtures",
        }
    return {
        "category_id": "encyclopedias",
        "parser_family": "dictionary_parser",
        "reason": "Inspect encyclopedia article structure before deciding its final parser family.",
        "risk": "high",
        "next_action": "complete rights and structure inspection before collecting exactly three allowlisted encyclopedia fixtures",
    }


def build_summary(base_dir: Path = Path("."), plan_path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    plan = load_json(base_dir / plan_path)
    pilots = verified_pilots(plan)
    comparisons = [compare_pilot(pilot, base_dir) for pilot in pilots]
    comparisons.sort(key=lambda item: item["category_id"])
    return {
        "summary_version": "pilot-category-validation-v1",
        "verified_categories": [item["category_id"] for item in comparisons],
        "verified_category_count": len(comparisons),
        "parser_families": sorted({item["parser_family"] for item in comparisons}),
        "category_comparisons": comparisons,
        "schema_coverage": schema_stress_test(comparisons),
        "next_recommended_pilot": next_pilot_recommendation(plan),
        "network_requests": 0,
        "llm_calls": 0,
    }


def render_report(summary: dict[str, Any]) -> str:
    rows = []
    for item in summary["category_comparisons"]:
        commentary = (
            f"{item['commentary_url_coverage']:.1%}"
            if item["commentary_url_coverage"] is not None
            else "N/A"
        )
        rows.append(
            f"| {item['category_tamil']} | `{item['parser_family']}` "
            f"| `{', '.join(item['record_types'])}` | {item['records_parsed']} "
            f"| {item['records_normalized']} | {item['validation_errors']} "
            f"| {item['required_field_coverage']:.1%} | {item['optional_field_coverage']:.1%} "
            f"| {item['source_url_coverage']:.1%} | {commentary} "
            f"| {item['metadata_completeness']:.1%} "
            f"| `{item['citation_readiness']['status']}` | {item['readiness_score']:.1f} |"
        )
    schema_rows = "\n".join(
        f"| `{item['schema_area']}` | `{item['status']}` | {item['evidence']} "
        f"| {item['recommended_change']} |"
        for item in summary["schema_coverage"]
    )
    usefulness = "\n".join(
        f"- **{item['category_tamil']}**: "
        + "; ".join(item["analytical_usefulness"]["uses"])
        for item in summary["category_comparisons"]
    )
    next_pilot = summary["next_recommended_pilot"]
    return f"""# Pilot Category Validation Report

## Executive Summary

- Verified pilots compared: `{summary['verified_category_count']}`
- Categories: `{', '.join(summary['verified_categories'])}`
- Parser families: `{', '.join(summary['parser_families'])}`
- Network requests: `0`
- LLM calls: `0`

The verified pilots validate the common schema envelope, deterministic IDs, Tamil text,
and exact source URLs across two verse traditions, one dictionary family, structured
grammar rules, and paragraph-based prose. The
comparison also exposes an intentional schema gap: commentary is
preserved, but not yet modeled as an independent record.

## Cross-Parser Comparison

| Category | Parser | Record Type | Parsed | Normalized | Errors | Required | Optional | Source URL | Commentary URL | Metadata | Citation | Readiness |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
{chr(10).join(rows)}

Optional-field coverage is descriptive, not a validation failure. Dictionary part of speech
is absent because the sampled source does not label it. Sangam `thurai` preserves source
colophon prose and is not treated as a controlled taxonomy. Grammar explanation coverage
is optional because commentary endpoints were outside its three-page fixture scope.

## Schema Stress Test

| Schema Area | Status | Evidence | Recommended Change |
| --- | --- | --- | --- |
{schema_rows}

## Analytical Usefulness

{usefulness}

## Risks

- Saivam evidence is a bounded Fourth Thirumurai seed, not all Saiva literature.
- Dictionary evidence is one entry from three fixture pages, not a dictionary-wide sample.
- Sangam evidence is three Natrinai poems from three fixture pages, not the anthology.
- Grammar evidence is two Nannul rules from three fixture pages, not the full work.
- Prose evidence is two synthetic paragraphs shaped by three inspected pages; source-text
  ingestion remains permission-gated.
- Optional fields differ legitimately across record types.
- Standalone commentary identity and relationships remain undefined.
- Dictionary sense segmentation and part-of-speech extraction need varied fixtures.

## Next Pilot Recommendation

Recommend **{next_pilot['category_id']}** using `{next_pilot['parser_family']}`.

{next_pilot['reason']}

Risk: `{next_pilot['risk']}`. Next action: `{next_pilot['next_action']}`.
This recommendation authorizes fixture planning only, not ingestion or category scraping.
"""


def write_outputs(
    summary: dict[str, Any],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and compare existing verified category pilots."
    )
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    try:
        summary = build_summary(args.base_dir)
        write_outputs(
            summary,
            output_path=args.base_dir / args.output,
            report_path=args.base_dir / args.report,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Verified categories: {summary['verified_category_count']}")
    print(f"Parser families: {len(summary['parser_families'])}")
    print(f"Next pilot: {summary['next_recommended_pilot']['category_id']}")
    print(f"Output: {args.output}")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
