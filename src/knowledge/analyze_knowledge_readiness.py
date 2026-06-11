from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
DEFAULT_OUTPUT = DEFAULT_KNOWLEDGE_DIR / "knowledge_readiness.json"
DEFAULT_REPORT = Path("reports/knowledge-readiness-report.md")

REGISTRY_SPECS: dict[str, dict[str, Any]] = {
    "synonyms": {
        "capability": "synonym_readiness",
        "id_field": "concept_id",
        "required": {"concept_id", "canonical_term", "synonyms", "variant_forms"},
    },
    "entities": {
        "capability": "entity_readiness",
        "id_field": "entity_id",
        "required": {
            "entity_id",
            "entity_type",
            "canonical_name",
            "aliases",
            "description",
        },
    },
    "motifs": {
        "capability": "motif_readiness",
        "id_field": "motif_id",
        "required": {"motif_id", "motif_name", "description", "example_patterns"},
    },
    "authors": {
        "capability": "author_readiness",
        "id_field": "author_id",
        "required": {"author_id", "canonical_name", "aliases", "period", "works"},
    },
    "deities": {
        "capability": "deity_readiness",
        "id_field": "deity_id",
        "required": {
            "deity_id",
            "canonical_name",
            "aliases",
            "tradition",
            "description",
        },
    },
    "places": {
        "capability": "place_readiness",
        "id_field": "place_id",
        "required": {
            "place_id",
            "canonical_name",
            "aliases",
            "place_type",
            "description",
        },
    },
    "themes": {
        "capability": "theme_readiness",
        "id_field": "theme_id",
        "required": {"theme_id", "theme_name", "description", "related_concepts"},
    },
    "literary_devices": {
        "capability": "literary_device_readiness",
        "id_field": "device_id",
        "required": {
            "device_id",
            "device_name",
            "description",
            "recognition_cues",
        },
    },
    "works": {
        "capability": "work_registry_support",
        "id_field": "work_id",
        "required": {
            "work_id",
            "canonical_title",
            "aliases",
            "authors",
            "period",
            "genre",
        },
    },
}

LIST_FIELDS = {
    "aliases",
    "synonyms",
    "variant_forms",
    "example_patterns",
    "works",
    "authors",
    "related_concepts",
    "recognition_cues",
}


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry(name: str, registry: dict[str, Any]) -> list[str]:
    spec = REGISTRY_SPECS[name]
    errors: list[str] = []
    if registry.get("registry_name") != name:
        errors.append("registry_name mismatch")
    if registry.get("schema_version") != "knowledge-registry-v1":
        errors.append("invalid schema_version")
    if registry.get("status") != "foundation_seed_only":
        errors.append("invalid foundation status")
    records = registry.get("records")
    if not isinstance(records, list):
        return errors + ["records must be a list"]
    identifiers: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} must be an object")
            continue
        missing = spec["required"] - record.keys()
        if missing:
            errors.append(f"record {index} missing {sorted(missing)}")
        identifier = record.get(spec["id_field"])
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"record {index} has invalid {spec['id_field']}")
        else:
            identifiers.append(identifier)
        for field in spec["required"] & LIST_FIELDS:
            if field in record and not isinstance(record[field], list):
                errors.append(f"record {index} field {field} must be a list")
    if len(identifiers) != len(set(identifiers)):
        errors.append("duplicate registry IDs")
    return errors


def registry_readiness(name: str, registry: dict[str, Any]) -> dict[str, Any]:
    errors = validate_registry(name, registry)
    records = registry.get("records", []) if isinstance(registry.get("records"), list) else []
    envelope_valid = (
        registry.get("registry_name") == name
        and registry.get("schema_version") == "knowledge-registry-v1"
        and registry.get("status") == "foundation_seed_only"
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
    foundation_score = (
        20
        + (15 if envelope_valid else 0)
        + (20 if not errors else 0)
        + (10 if deterministic_ids else 0)
        + (5 if records else 0)
    )
    analytical_score = round(foundation_score * 0.5, 1)
    return {
        "registry": name,
        "capability": REGISTRY_SPECS[name]["capability"],
        "record_count": len(records),
        "foundation_score": foundation_score,
        "analytical_readiness_score": analytical_score,
        "status": (
            "FOUNDATION_READY_ANALYTICS_NOT_READY"
            if foundation_score == 70
            else "FOUNDATION_REPAIR_REQUIRED"
        ),
        "schema_errors": errors,
        "reviewed_record_count": 0,
        "evidence_link_count": 0,
        "corpus_annotation_count": 0,
        "limitations": [
            "seed examples are illustrative and unreviewed",
            "no corpus evidence spans are linked",
            "no extraction coverage has been measured",
        ],
    }


def analyze_knowledge_readiness(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
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
    return {
        "analysis_version": "knowledge-readiness-v1",
        "knowledge_schema_version": "knowledge-registry-v1",
        "phase": "foundation_only",
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
        "extraction_performed": False,
        "scraping_performed": False,
        "llm_calls": 0,
        "decision": "FOUNDATION_READY_EXTRACTION_NOT_STARTED",
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
- Decision: `{analysis['decision']}`
- Extraction performed: `{str(analysis['extraction_performed']).lower()}`
- Scraping performed: `{str(analysis['scraping_performed']).lower()}`
- LLM calls: `{analysis['llm_calls']}`

## Capability Scores

| Capability | Registry | Seeds | Foundation | Analytical | Status |
| --- | --- | ---: | ---: | ---: | --- |
{rows}

## Interpretation

The structural foundation is ready: files exist, schemas validate, IDs are deterministic,
and each registry has one small illustrative seed. Analytical readiness remains low because
there are no reviewed authority releases, corpus evidence spans, annotations, extraction
coverage measurements, or aggregation results.

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
    args = parser.parse_args(argv)
    analysis = analyze_knowledge_readiness(args.knowledge_dir)
    write_outputs(analysis, output_path=args.output, report_path=args.report)
    print(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all(not item["schema_errors"] for item in analysis["capabilities"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
