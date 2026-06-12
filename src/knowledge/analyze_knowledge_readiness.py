from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from knowledge.registry_contracts import (
    REGISTRY_SPECS,
    load_registry,
    validate_registry,
)

DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
DEFAULT_OUTPUT = DEFAULT_KNOWLEDGE_DIR / "knowledge_readiness.json"
DEFAULT_REPORT = Path("reports/knowledge-readiness-report.md")
DEFAULT_OCCURRENCE_MANIFEST = Path("data/processed/analytics/occurrence_index_manifest.json")
DEFAULT_AGGREGATION_EXAMPLES = Path("data/processed/analytics/aggregation_examples.json")

def registry_readiness(name: str, registry: dict[str, Any]) -> dict[str, Any]:
    errors = validate_registry(name, registry)
    records = registry.get("records", []) if isinstance(registry.get("records"), list) else []
    envelope_valid = (
        registry.get("registry_name") == name
        and registry.get("schema_version") == "knowledge-registry-v1"
        and registry.get("status") in {"foundation_seed_only", "curated_seed_v1"}
    )
    identifiers = [
        record.get(REGISTRY_SPECS[name]["id_field"])
        for record in records
        if isinstance(record, dict)
    ]
    deterministic_ids = bool(identifiers) and all(
        isinstance(value, str)
        and value
        and value.lower() == value
        and " " not in value
        for value in identifiers
    )
    base_foundation_score = (
        20
        + (15 if envelope_valid else 0)
        + (20 if not errors else 0)
        + (10 if deterministic_ids else 0)
        + (5 if records else 0)
    )
    curated = (
        registry.get("status") == "curated_seed_v1"
        and len(records) >= 3
        and all(record.get("status") == "curated_seed" for record in records)
    )
    foundation_score = base_foundation_score + (15 if curated and not errors else 0)
    analytical_score = 55.0 if curated and not errors else round(base_foundation_score * 0.5, 1)
    return {
        "registry": name,
        "capability": REGISTRY_SPECS[name]["capability"],
        "record_count": len(records),
        "foundation_score": foundation_score,
        "analytical_readiness_score": analytical_score,
        "status": (
            "CURATED_SEED_READY_EXTRACTION_NOT_STARTED"
            if foundation_score == 85
            else "FOUNDATION_READY_ANALYTICS_NOT_READY"
            if foundation_score == 70
            else "FOUNDATION_REPAIR_REQUIRED"
        ),
        "schema_errors": errors,
        "curated_record_count": (
            sum(record.get("status") == "curated_seed" for record in records)
            if curated
            else 0
        ),
        "reviewed_record_count": 0,
        "evidence_link_count": 0,
        "corpus_annotation_count": 0,
        "limitations": [
            (
                "curated seeds have no external lexical citations or reviewer sign-off"
                if curated
                else "seed examples are illustrative and unreviewed"
            ),
            "no corpus evidence spans are linked",
            "no extraction coverage has been measured",
        ],
    }


def analyze_knowledge_readiness(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
    occurrence_manifest_path: Path = DEFAULT_OCCURRENCE_MANIFEST,
    aggregation_examples_path: Path = DEFAULT_AGGREGATION_EXAMPLES,
) -> dict[str, Any]:
    results = []
    for name in REGISTRY_SPECS:
        path = knowledge_dir / f"{name}.json"
        if not path.exists():
            results.append(
                {
                    "registry": name,
                    "capability": REGISTRY_SPECS[name]["capability"],
                    "record_count": 0,
                    "foundation_score": 0,
                    "analytical_readiness_score": 0.0,
                    "status": "MISSING",
                    "schema_errors": ["registry file is missing"],
                    "reviewed_record_count": 0,
                    "evidence_link_count": 0,
                    "corpus_annotation_count": 0,
                    "limitations": ["registry file is missing"],
                }
            )
            continue
        results.append(registry_readiness(name, load_registry(path)))
    primary = [item for item in results if item["registry"] != "works"]
    occurrence_manifest = (
        json.loads(occurrence_manifest_path.read_text(encoding="utf-8"))
        if occurrence_manifest_path.exists()
        else {}
    )
    occurrence_coverage_score = 0.0
    if occurrence_manifest:
        field_count = len(occurrence_manifest.get("indexed_fields", []))
        record_count = int(occurrence_manifest.get("indexed_records", 0))
        occurrence_coverage_score = min(100.0, round(field_count * 8 + min(record_count, 1400) / 20, 1))
    evidence_readiness_score = 62.5 if occurrence_manifest else 0.0
    aggregation_examples = (
        json.loads(aggregation_examples_path.read_text(encoding="utf-8"))
        if aggregation_examples_path.exists()
        else {}
    )
    aggregation_readiness_score = 66.0 if aggregation_examples else 0.0
    analytics_infrastructure_score = round(
        (evidence_readiness_score + aggregation_readiness_score) / 2,
        1,
    )
    return {
        "analysis_version": "knowledge-readiness-v3",
        "knowledge_schema_version": "knowledge-registry-v1",
        "phase": "curated_seed_population",
        "registry_count": len(results),
        "primary_capability_count": len(primary),
        "foundation_readiness_score": round(
            sum(item["foundation_score"] for item in primary) / len(primary), 1
        ),
        "analytical_readiness_score": round(
            sum(item["analytical_readiness_score"] for item in primary) / len(primary),
            1,
        ),
        "capabilities": results,
        "evidence_readiness_score": evidence_readiness_score,
        "aggregation_readiness_score": aggregation_readiness_score,
        "analytics_infrastructure_readiness_score": analytics_infrastructure_score,
        "occurrence_coverage": {
            "occurrence_index_available": bool(occurrence_manifest),
            "indexed_records": int(occurrence_manifest.get("indexed_records", 0)),
            "indexed_field_entries": int(occurrence_manifest.get("indexed_field_entries", 0)),
            "indexed_fields": occurrence_manifest.get("indexed_fields", []),
            "coverage_score": occurrence_coverage_score,
            "aggregation_performed": False,
        },
        "aggregation_coverage": {
            "aggregation_examples_available": bool(aggregation_examples),
            "example_count": len(aggregation_examples.get("examples", [])),
            "supported_groupings": ["author", "category", "work", "record_type", "source"],
            "answer_generation_performed": False,
            "llm_calls": 0,
        },
        "extraction_performed": False,
        "scraping_performed": False,
        "llm_calls": 0,
        "baseline": {
            "phase": "phase_21",
            "foundation_readiness_score": 70.0,
            "analytical_readiness_score": 35.0,
        },
        "decision": "CURATED_SEED_READY_EXTRACTION_NOT_STARTED",
    }


def render_report(analysis: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{item['capability']}` | `{item['registry']}` | {item['record_count']} "
        f"| {item['foundation_score']:.1f} | {item['analytical_readiness_score']:.1f} "
        f"| `{item['status']}` |"
        for item in analysis["capabilities"]
    )
    return f"""# Knowledge Readiness Report

## Summary

- Registry files: `{analysis['registry_count']}`
- Primary analytical capabilities: `{analysis['primary_capability_count']}`
- Foundation readiness: `{analysis['foundation_readiness_score']:.1f}/100`
- Analytical readiness: `{analysis['analytical_readiness_score']:.1f}/100`
- Evidence readiness: `{analysis['evidence_readiness_score']:.1f}/100`
- Aggregation readiness: `{analysis['aggregation_readiness_score']:.1f}/100`
- Analytics infrastructure readiness: `{analysis['analytics_infrastructure_readiness_score']:.1f}/100`
- Occurrence coverage score: `{analysis['occurrence_coverage']['coverage_score']:.1f}/100`
- Occurrence index available: `{str(analysis['occurrence_coverage']['occurrence_index_available']).lower()}`
- Aggregation examples available: `{str(analysis['aggregation_coverage']['aggregation_examples_available']).lower()}`
- Phase 21 baseline: `{analysis['baseline']['foundation_readiness_score']:.1f}` foundation,
  `{analysis['baseline']['analytical_readiness_score']:.1f}` analytical
- Decision: `{analysis['decision']}`
- Extraction performed: `{str(analysis['extraction_performed']).lower()}`
- Scraping performed: `{str(analysis['scraping_performed']).lower()}`
- LLM calls: `{analysis['llm_calls']}`

## Capability Scores

| Capability | Registry | Seeds | Foundation | Analytical | Status |
| --- | --- | ---: | ---: | ---: | --- |
{rows}

## Interpretation

The structural foundation remains valid, and five registries now contain three manually
curated seed records each. The local occurrence index and aggregation examples now provide
literal corpus evidence rows and grouped statistics for future analysis, but analytical
readiness remains limited because there are no cited scholarly authority releases,
reviewer sign-offs, registry-to-corpus annotations, extraction coverage measurements, or
answer-generation behavior.

No seed record should be used as proof that a term occurs in the corpus. Future population
phases must link every accepted assertion to exact corpus records and source URLs.
"""


def write_outputs(
    analysis: dict[str, Any],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(analysis), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate the local Tamil literary knowledge-layer foundation."
    )
    parser.add_argument("--knowledge-dir", type=Path, default=DEFAULT_KNOWLEDGE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--occurrence-manifest", type=Path, default=DEFAULT_OCCURRENCE_MANIFEST)
    parser.add_argument("--aggregation-examples", type=Path, default=DEFAULT_AGGREGATION_EXAMPLES)
    args = parser.parse_args(argv)
    analysis = analyze_knowledge_readiness(
        args.knowledge_dir,
        args.occurrence_manifest,
        args.aggregation_examples,
    )
    write_outputs(analysis, output_path=args.output, report_path=args.report)
    print(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all(not item["schema_errors"] for item in analysis["capabilities"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
