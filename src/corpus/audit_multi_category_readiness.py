from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.pilot_ingest_category import load_json
from corpus.validate_pilot_categories import (
    REQUIRED_FIELDS,
    build_summary,
    coverage,
    load_verified_records,
    verified_pilots,
)

DEFAULT_REGISTRY = Path(
    "data/processed/corpus_registry/website_category_registry.json"
)
DEFAULT_PLAN = Path("data/processed/corpus_registry/pilot_category_plan.json")
DEFAULT_OUTPUT = Path(
    "data/processed/audits/multi_category_readiness_audit.json"
)
DEFAULT_REPORT = Path("reports/multi-category-readiness-audit-report.md")

SUPPORTED_RECORD_TYPES = {
    "verse",
    "hymn",
    "prose_section",
    "grammar_rule",
    "dictionary_entry",
    "encyclopedia_entry",
    "manuscript_image",
    "external_reference",
}
VERIFIED_CATEGORY_IDS = {
    "grammar",
    "saivam",
    "sangam_literature",
    "dictionaries",
    "twentieth_century_prose",
}
VERIFIED_PARSER_FAMILIES = {
    "grammar_parser",
    "verse_parser",
    "dictionary_parser",
    "prose_parser",
}
NOT_READY_FAMILIES = {"mixed_parser", "image_metadata_parser"}

ANALYTICS_READINESS = [
    {
        "capability": "synonym_analysis",
        "score": 55,
        "status": "partial",
        "evidence": "Dictionary structure is proven, but only one entry and no nigandu semantic groups are verified.",
    },
    {
        "capability": "motif_analysis",
        "score": 72,
        "status": "partial",
        "evidence": "Two poetry traditions are represented, but motifs are not normalized annotations.",
    },
    {
        "capability": "entity_analysis",
        "score": 40,
        "status": "partial",
        "evidence": "Authors and selected literary metadata exist; generalized entity extraction and confidence are absent.",
    },
    {
        "capability": "deity_analysis",
        "score": 75,
        "status": "partial",
        "evidence": "Saivam supplies devotional evidence, but deity normalization is not proven across traditions.",
    },
    {
        "capability": "author_comparison",
        "score": 90,
        "status": "ready",
        "evidence": "Saivam and Sangam records preserve normalized author identity and source citations.",
    },
    {
        "capability": "cross_corpus_comparison",
        "score": 85,
        "status": "ready",
        "evidence": "The common envelope supports two verse traditions plus lexical evidence without flattening their identities.",
    },
    {
        "capability": "grammar_rule_analysis",
        "score": 65,
        "status": "partial",
        "evidence": "Numbered Nannul rules are structured, but explanations, examples, exceptions, and cross-rule links remain unverified.",
    },
    {
        "capability": "prose_style_analysis",
        "score": 62,
        "status": "partial",
        "evidence": "Paragraph records and author metadata are structured, but source-text and multi-section evidence remain rights-gated.",
    },
]

PARSER_RISKS = {
    "verse_parser": (
        "Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures."
    ),
    "dictionary_parser": (
        "Sense order, examples, cross-references, and encyclopedia article structure are not generally proven."
    ),
    "grammar_parser": (
        "Sutra, explanation, example, exception, and commentator boundaries are unverified."
    ),
    "prose_parser": (
        "Paragraph structure is proven; chapter transitions, pages, footnotes, editions, and permissioned source text remain unverified."
    ),
    "mixed_parser": (
        "No dispatch contract has been proven for pages combining verse, prose, tables, or media."
    ),
    "image_metadata_parser": (
        "Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified."
    ),
    "table_parser": (
        "Column identity, multilingual cells, repeated headers, and domain labels are unverified."
    ),
    "external_link_registry": (
        "Institution, robots, rights, scope, and approval metadata need a registry-only pilot."
    ),
}


def round_score(value: float) -> float:
    return round(value, 1)


def load_verified_evidence(
    base_dir: Path, plan: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for pilot in verified_pilots(plan):
        _, normalized, evidence_path = load_verified_records(pilot, base_dir)
        records.extend(normalized)
        evidence.append(
            {
                "category_id": pilot["category_id"],
                "parser_family": pilot["parser_family"],
                "record_count": len(normalized),
                "evidence_path": evidence_path,
            }
        )
    return records, sorted(evidence, key=lambda item: item["category_id"])


def field_coverage(records: list[dict[str, Any]], field: str) -> float:
    return coverage(records, [field])


def architecture_status(category: dict[str, Any]) -> tuple[str, str, str]:
    category_id = category["category_id"]
    family = category["parser_family"]
    if category_id in VERIFIED_CATEGORY_IDS:
        return (
            "ready",
            "Bounded pilot evidence validates parser output, schema mapping, and provenance.",
            "Retain bounded expansion gates and sample structural variants before scale.",
        )
    if category_id == "encyclopedias":
        return (
            "not_ready",
            "The registry assigns dictionary_parser, but mixed article, reference, table, and media structure is unproven.",
            "Inspect three fixtures and decide whether a dedicated encyclopedia adapter is required.",
        )
    if family in NOT_READY_FAMILIES:
        return (
            "not_ready",
            PARSER_RISKS[family],
            "Run source inspection and a three-fixture parser-family pilot before ingestion.",
        )
    if family in VERIFIED_PARSER_FAMILIES:
        return (
            "partial",
            PARSER_RISKS[family],
            "Collect three work-specific fixtures and validate hierarchy before ingestion.",
        )
    return (
        "partial",
        PARSER_RISKS[family],
        "Validate this parser family with three allowlisted fixtures and schema-specific tests.",
    )


def category_matrix(registry: dict[str, Any]) -> list[dict[str, str]]:
    matrix = []
    for category in registry.get("categories", []):
        status, risk, next_step = architecture_status(category)
        matrix.append(
            {
                "category_id": category["category_id"],
                "category_tamil": category["category_tamil"],
                "category_english": category["category_english"],
                "content_type": category["content_type"],
                "expected_parser_family": category["parser_family"],
                "architecture_status": status,
                "major_risk": risk,
                "recommended_next_step": next_step,
            }
        )
    return matrix


def parser_matrix(registry: dict[str, Any]) -> list[dict[str, Any]]:
    counts = Counter(
        category["parser_family"] for category in registry.get("categories", [])
    )
    rows = []
    for family in sorted(counts):
        verified = family in VERIFIED_PARSER_FAMILIES
        rows.append(
            {
                "parser_family": family,
                "category_count": counts[family],
                "status": "pilot_verified" if verified else "stub_unverified",
                "compatible_with_schema_v2": True,
                "major_gap": PARSER_RISKS[family],
            }
        )
    return rows


def schema_assessment(
    pilot_summary: dict[str, Any], records: list[dict[str, Any]]
) -> dict[str, Any]:
    common_coverage = round_score(
        sum(field_coverage(records, field) for field in REQUIRED_FIELDS)
        / len(REQUIRED_FIELDS)
        * 100
    )
    observed_types = sorted(
        {str(record.get("record_type")) for record in records if record.get("record_type")}
    )
    record_type_evidence = len(observed_types) / len(SUPPORTED_RECORD_TYPES) * 100
    stress_values = {"supported": 100, "partial": 50, "not_supported": 0}
    stress_score = (
        sum(stress_values[item["status"]] for item in pilot_summary["schema_coverage"])
        / len(pilot_summary["schema_coverage"])
    )
    score = round_score(
        common_coverage * 0.55
        + stress_score * 0.20
        + record_type_evidence * 0.25
    )
    return {
        "score": score,
        "common_required_field_coverage": common_coverage,
        "observed_record_types": observed_types,
        "supported_record_type_count": len(SUPPORTED_RECORD_TYPES),
        "record_type_evidence_coverage": round_score(record_type_evidence),
        "schema_stress_score": round_score(stress_score),
        "field_reuse": {
            "status": "strong",
            "evidence": "All verified records reuse stable identity, category, work, content, language, source, and parser fields.",
        },
        "field_sparsity": {
            "status": "expected_but_requires_contracts",
            "evidence": "Optional poetry and lexical fields are intentionally sparse across record types.",
        },
        "category_specific_gaps": [
            "Standalone commentary identity and relationships are partial.",
            "Grammar examples, exceptions, commentator identity, and cross-rule links are unverified.",
            "Prose paragraphs are supported, but page, footnote, edition, and permissioned source-text fields remain partial.",
            "Encyclopedia references/media and manuscript/OCR contracts are unverified.",
        ],
    }


def parser_assessment(
    comparisons: list[dict[str, Any]], parsers: list[dict[str, Any]]
) -> dict[str, Any]:
    family_coverage = (
        sum(row["status"] == "pilot_verified" for row in parsers) / len(parsers) * 100
    )
    validation_consistency = (
        sum(item["validation_status"] == "VALID" for item in comparisons)
        / len(comparisons)
        * 100
    )
    output_compatibility = (
        sum(item["required_field_coverage"] for item in comparisons)
        / len(comparisons)
        * 100
    )
    score = round_score(
        family_coverage * 0.50
        + validation_consistency * 0.25
        + output_compatibility * 0.25
    )
    return {
        "score": score,
        "verified_parser_families": sorted(VERIFIED_PARSER_FAMILIES),
        "total_parser_families": len(parsers),
        "parser_family_coverage": round_score(family_coverage),
        "validation_consistency": round_score(validation_consistency),
        "output_compatibility": round_score(output_compatibility),
        "matrix": parsers,
    }


def metadata_assessment(records: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ("author", "title", "source_url", "category_id")
    coverages = {
        field: round_score(field_coverage(records, field) * 100) for field in fields
    }
    score = round_score(sum(coverages.values()) / len(coverages))
    return {
        "score": score,
        "author_coverage": coverages["author"],
        "title_coverage": coverages["title"],
        "source_coverage": coverages["source_url"],
        "category_coverage": coverages["category_id"],
        "note": "Dictionary author is legitimately absent in the sampled entry; coverage is descriptive, not fabricated.",
    }


def citation_assessment(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    source = (
        sum(item["citation_readiness"]["source_url_coverage"] for item in comparisons)
        / len(comparisons)
        * 100
    )
    identity = (
        sum(item["citation_readiness"]["identity_coverage"] for item in comparisons)
        / len(comparisons)
        * 100
    )
    citation_text = (
        sum(item["citation_readiness"]["citation_text_coverage"] for item in comparisons)
        / len(comparisons)
        * 100
    )
    score = round_score(source * 0.45 + identity * 0.45 + citation_text * 0.10)
    return {
        "score": score,
        "source_url_coverage": round_score(source),
        "identity_traceability": round_score(identity),
        "citation_text_coverage": round_score(citation_text),
        "status": "strong",
    }


def analytics_assessment() -> dict[str, Any]:
    score = round_score(
        sum(item["score"] for item in ANALYTICS_READINESS)
        / len(ANALYTICS_READINESS)
    )
    return {"score": score, "capabilities": ANALYTICS_READINESS}


def expansion_assessment(matrix: list[dict[str, str]]) -> dict[str, Any]:
    values = {"ready": 100, "partial": 55, "not_ready": 20}
    counts = Counter(item["architecture_status"] for item in matrix)
    score = round_score(
        sum(values[item["architecture_status"]] for item in matrix) / len(matrix)
    )
    return {
        "score": score,
        "category_count": len(matrix),
        "status_counts": dict(sorted(counts.items())),
        "website_wide_answer": "PARTIAL_NOT_SCALE_READY",
        "answer": (
            "The common architecture can represent all 32 categories at a registry and provenance level, "
            "but only five categories and four parser families have extraction evidence. Mixed, image, "
            "encyclopedia, and several structured-text families require pilots."
        ),
    }


def recommendation() -> dict[str, str]:
    return {
        "category_id": "encyclopedias",
        "parser_family": "parser_family_review_required",
        "decision": "RECOMMENDED_NEXT_SOURCE_INSPECTION",
        "reason": (
            "Prose now validates the fourth parser family and the first paragraph-based hierarchy. "
            "The remaining planned pilot is encyclopedia content, but inspection must decide whether "
            "dictionary_parser is sufficient or a dedicated article adapter is needed."
        ),
        "precondition": (
            "Complete source rights and mixed-content structure review before collecting encyclopedia fixtures."
        ),
        "why_not_encyclopedia": (
            "Encyclopedia is now the next inspection target, not yet an ingestion target."
        ),
        "next_action": "Inspect article, reference, table, cross-link, and media boundaries before selecting the parser family.",
    }


def future_category_readiness() -> list[dict[str, str]]:
    return [
        {
            "category": "grammar",
            "status": "ready",
            "evidence": "Nannul fixtures validate numbered grammar_rule records, hierarchy, citations, and deterministic identity.",
            "major_risk": "Examples, exceptions, commentator identity, and explanation parsing need broader fixtures.",
        },
        {
            "category": "prose",
            "status": "ready",
            "evidence": "Three inspected pages and rights-safe fixtures validate paragraph-level prose_section records and rights metadata.",
            "major_risk": "Permissioned source text, chapters, pages, footnotes, and edition boundaries remain unproven.",
        },
        {
            "category": "encyclopedias",
            "status": "not_ready",
            "evidence": "The dictionary envelope is reusable, but the assigned parser has no article/media evidence.",
            "major_risk": "Flattening sections, references, cross-links, tables, and media into a definition.",
        },
        {
            "category": "mixed_content",
            "status": "not_ready",
            "evidence": "MixedParser is a conservative schema stub with no proven source dispatch.",
            "major_risk": "Losing relationships between verse, prose, commentary, tables, and assets.",
        },
    ]


def build_audit(base_dir: Path = Path(".")) -> dict[str, Any]:
    registry = load_json(base_dir / DEFAULT_REGISTRY)
    plan = load_json(base_dir / DEFAULT_PLAN)
    records, evidence = load_verified_evidence(base_dir, plan)
    pilot_summary = build_summary(base_dir)
    comparisons = pilot_summary["category_comparisons"]
    categories = category_matrix(registry)
    parsers = parser_matrix(registry)
    schema = schema_assessment(pilot_summary, records)
    parser = parser_assessment(comparisons, parsers)
    metadata = metadata_assessment(records)
    citation = citation_assessment(comparisons)
    analytics = analytics_assessment()
    expansion = expansion_assessment(categories)
    scores = {
        "schema_readiness": schema["score"],
        "parser_readiness": parser["score"],
        "metadata_readiness": metadata["score"],
        "citation_readiness": citation["score"],
        "analytics_readiness": analytics["score"],
        "expansion_readiness": expansion["score"],
    }
    scores["overall_readiness"] = round_score(
        sum(scores.values()) / len(scores)
    )
    return {
        "audit_version": "multi-category-readiness-v1",
        "schema_version": "website-corpus-v2",
        "source_site": registry["source_site"],
        "verified_category_count": len(evidence),
        "verified_record_count": len(records),
        "verified_evidence": evidence,
        "readiness_scores": scores,
        "schema_readiness": schema,
        "parser_readiness": parser,
        "metadata_readiness": metadata,
        "citation_readiness": citation,
        "analytics_readiness": analytics,
        "expansion_readiness": expansion,
        "category_readiness_matrix": categories,
        "future_category_readiness": future_category_readiness(),
        "strategic_recommendation": recommendation(),
        "architecture_strengths": [
            "Stable source-scoped IDs and a shared provenance envelope work across verse, dictionary, grammar, and prose records.",
            "Two poetry traditions retain distinct hierarchy without schema fragmentation.",
            "Numbered grammar rules retain chapter, section, rule text, and commentary traceability.",
            "Prose paragraphs retain ordered section identity, authorship, rights status, and source traceability.",
            "All verified records retain exact source URLs and validation passes with zero errors.",
            "Raw/processed/report separation and fixture-first testing support controlled expansion.",
        ],
        "architecture_weaknesses": [
            "Only four of eight parser families have bounded source evidence.",
            "Standalone commentary, entity, motif, and normalized literary-concept contracts remain incomplete.",
            "Mixed-content dispatch and encyclopedia article modeling are not proven.",
            "Image/manuscript rights, asset metadata, transcription, and OCR provenance are not proven.",
        ],
        "scaling_risks": [
            "Treating a shared schema envelope as proof that source-specific parsers are interchangeable.",
            "Flattening work-specific hierarchy when expanding verse_parser to new traditions.",
            "Using dictionary_parser for encyclopedias without proving article and media boundaries.",
            "Scaling prose from structural fixtures before written permission, edition, page, and footnote metadata are explicit.",
            "Introducing OCR or mixed-content ingestion without confidence and source-image traceability.",
        ],
        "network_requests": 0,
        "llm_calls": 0,
        "corpus_mutations": 0,
    }


def render_report(audit: dict[str, Any]) -> str:
    scores = audit["readiness_scores"]
    score_rows = "\n".join(
        f"| `{name}` | {value:.1f} |"
        for name, value in scores.items()
    )
    parser_rows = "\n".join(
        f"| `{row['parser_family']}` | {row['category_count']} | `{row['status']}` "
        f"| {row['major_gap']} |"
        for row in audit["parser_readiness"]["matrix"]
    )
    category_rows = "\n".join(
        f"| `{row['category_id']}` | {row['category_tamil']} "
        f"| `{row['expected_parser_family']}` | `{row['architecture_status']}` "
        f"| {row['major_risk']} | {row['recommended_next_step']} |"
        for row in audit["category_readiness_matrix"]
    )
    analytics_rows = "\n".join(
        f"| `{row['capability']}` | {row['score']} | `{row['status']}` | {row['evidence']} |"
        for row in audit["analytics_readiness"]["capabilities"]
    )
    future_rows = "\n".join(
        f"| `{row['category']}` | `{row['status']}` | {row['evidence']} | {row['major_risk']} |"
        for row in audit["future_category_readiness"]
    )
    strengths = "\n".join(f"- {item}" for item in audit["architecture_strengths"])
    weaknesses = "\n".join(f"- {item}" for item in audit["architecture_weaknesses"])
    risks = "\n".join(f"- {item}" for item in audit["scaling_risks"])
    recommendation = audit["strategic_recommendation"]
    return f"""# Multi-Category Readiness Audit Report

## Executive Summary

- Verified categories: `{audit['verified_category_count']}`
- Verified records inspected: `{audit['verified_record_count']}`
- TamilVU registry categories assessed: `{audit['expansion_readiness']['category_count']}`
- Overall readiness: `{scores['overall_readiness']:.1f}/100`
- Website-wide decision: `{audit['expansion_readiness']['website_wide_answer']}`
- Network requests: `0`
- LLM calls: `0`
- Frozen corpus mutations: `0`

Five pilots now exercise two distinct poetry hierarchies, one lexical hierarchy, one
grammar-rule hierarchy, and paragraph-based prose through the same identity, provenance,
validation, and normalization envelope. They are not sufficient to declare the remaining
parser families production-ready.

## Readiness Scores

| Dimension | Score |
| --- | ---: |
{score_rows}

Scores are deterministic weighted evidence summaries. Schema emphasizes common-field
coverage while discounting unobserved record types. Parser readiness gives half its weight
to verified family coverage. Expansion readiness maps each category as ready `100`,
partial `55`, or not ready `20`. Overall readiness is the unweighted mean of the six
dimensions, preventing strong citations from hiding weak parser coverage.

## Evidence Learned

- **Saivam:** proves hymn/verse/commentary identity, author, devotional metadata, and exact source traceability.
- **Sangam:** proves anthology poem identity, thinai, situation, poet, colophon, and line preservation.
- **Dictionaries:** proves headword-definition records and lexical content without inventing absent part-of-speech metadata.
- **Grammar:** proves numbered rule text, chapter/section hierarchy, and exact commentary traceability.
- **Prose:** proves paragraph segmentation, section identity, authorship, rights status, and exact source traceability.

## Schema Readiness

Common required-field coverage is `{audit['schema_readiness']['common_required_field_coverage']:.1f}%`.
Observed record-type evidence covers `{audit['schema_readiness']['record_type_evidence_coverage']:.1f}%`
of the eight schema v2 record types. The shared envelope is strong, but standalone
commentary, encyclopedia, and image contracts remain partly or wholly
unverified.

## Parser Readiness Matrix

| Parser Family | Registry Categories | Status | Major Gap |
| --- | ---: | --- | --- |
{parser_rows}

## Metadata And Citation

- Author coverage: `{audit['metadata_readiness']['author_coverage']:.1f}%`
- Title coverage: `{audit['metadata_readiness']['title_coverage']:.1f}%`
- Source coverage: `{audit['metadata_readiness']['source_coverage']:.1f}%`
- Category coverage: `{audit['metadata_readiness']['category_coverage']:.1f}%`
- Citation source URL coverage: `{audit['citation_readiness']['source_url_coverage']:.1f}%`
- Citation identity traceability: `{audit['citation_readiness']['identity_traceability']:.1f}%`

## Literary Analytics Readiness

| Capability | Score | Status | Evidence |
| --- | ---: | --- | --- |
{analytics_rows}

## Future Category Readiness

| Category Family | Status | Evidence | Major Risk |
| --- | --- | --- | --- |
{future_rows}

## Can The Current Architecture Support All 32 TamilVU Categories?

**Partially.** The registry, common schema, stable IDs, and provenance envelope can name
and trace all 32 categories. The extraction architecture is not scale-ready because only
four parser families have source evidence and mixed/image families remain unproven.

Status counts: `{json.dumps(audit['expansion_readiness']['status_counts'], sort_keys=True)}`.

## Category Readiness Matrix

| Category ID | Tamil Category | Expected Parser | Status | Major Risk | Recommended Next Step |
| --- | --- | --- | --- | --- | --- |
{category_rows}

## Architecture Strengths

{strengths}

## Architecture Weaknesses

{weaknesses}

## Scaling Risks

{risks}

## Strategic Recommendation

Choose **encyclopedia source inspection** with `{recommendation['parser_family']}`.

{recommendation['reason']}

- **Precondition:** {recommendation['precondition']}
- **Why not encyclopedia yet:** {recommendation['why_not_encyclopedia']}
- **Next action:** {recommendation['next_action']}
"""


def write_outputs(
    audit: dict[str, Any],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(audit), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit website-wide readiness using verified local pilot evidence."
    )
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    try:
        audit = build_audit(args.base_dir)
        write_outputs(
            audit,
            output_path=args.base_dir / args.output,
            report_path=args.base_dir / args.report,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Verified categories: {audit['verified_category_count']}")
    print(f"Registry categories: {audit['expansion_readiness']['category_count']}")
    print(f"Overall readiness: {audit['readiness_scores']['overall_readiness']:.1f}")
    print(f"Next pilot: {audit['strategic_recommendation']['category_id']}")
    print(f"Output: {args.output}")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
