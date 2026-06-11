from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from knowledge.analyze_knowledge_readiness import analyze_knowledge_readiness
from knowledge.registry_contracts import REGISTRY_SPECS, load_registry, validate_registry

DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
DEFAULT_SUMMARY = DEFAULT_KNOWLEDGE_DIR / "knowledge_seed_summary.json"
DEFAULT_REPORT = Path("reports/knowledge-seed-quality-report.md")


def registry_digest(registry: dict[str, Any]) -> str:
    canonical = json.dumps(
        registry, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_validation_summary(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
) -> dict[str, Any]:
    registry_counts: dict[str, int] = {}
    curated_entries: dict[str, int] = {}
    lexical_form_counts: dict[str, int] = {}
    validation_errors: dict[str, list[str]] = {}
    registry_digests: dict[str, str] = {}
    for name in REGISTRY_SPECS:
        path = knowledge_dir / f"{name}.json"
        if not path.exists():
            registry_counts[name] = 0
            curated_entries[name] = 0
            validation_errors[name] = ["registry file is missing"]
            lexical_form_counts[name] = 0
            continue
        registry = load_registry(path)
        records = registry.get("records", [])
        registry_counts[name] = len(records) if isinstance(records, list) else 0
        curated_entries[name] = (
            sum(record.get("status") == "curated_seed" for record in records)
            if isinstance(records, list)
            else 0
        )
        spec = REGISTRY_SPECS[name]
        lexical_form_counts[name] = (
            sum(
                1
                + sum(
                    len(record.get(field, []))
                    for field in spec["alias_fields"]
                    if isinstance(record.get(field, []), list)
                )
                for record in records
                if isinstance(record, dict)
            )
            if isinstance(records, list)
            else 0
        )
        errors = validate_registry(name, registry)
        if errors:
            validation_errors[name] = errors
        registry_digests[name] = registry_digest(registry)

    readiness = analyze_knowledge_readiness(knowledge_dir)
    return {
        "summary_version": "knowledge-seed-summary-v1",
        "registry_counts": dict(sorted(registry_counts.items())),
        "curated_entries": dict(sorted(curated_entries.items())),
        "lexical_form_counts": dict(sorted(lexical_form_counts.items())),
        "readiness_scores": {
            "foundation": readiness["foundation_readiness_score"],
            "analytical": readiness["analytical_readiness_score"],
            "baseline_foundation": readiness["baseline"]["foundation_readiness_score"],
            "baseline_analytical": readiness["baseline"]["analytical_readiness_score"],
        },
        "registry_digests": dict(sorted(registry_digests.items())),
        "validation_errors": validation_errors,
        "status": "VALID" if not validation_errors else "INVALID",
        "extraction_performed": False,
        "scraping_performed": False,
        "llm_calls": 0,
    }


def render_quality_report(summary: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{name}` | {count} | {summary['curated_entries'][name]} |"
        for name, count in summary["registry_counts"].items()
    )
    scores = summary["readiness_scores"]
    return f"""# Knowledge Seed Quality Report

## Summary

- Validation: `{summary['status']}`
- Registry files: `{len(summary['registry_counts'])}`
- Total records: `{sum(summary['registry_counts'].values())}`
- Curated records: `{sum(summary['curated_entries'].values())}`
- Foundation readiness: `{scores['foundation']:.1f}/100`
- Analytical readiness: `{scores['analytical']:.1f}/100`
- Phase 21 baseline: `{scores['baseline_foundation']:.1f}` foundation,
  `{scores['baseline_analytical']:.1f}` analytical
- Extraction performed: `false`
- Scraping performed: `false`
- LLM calls: `0`

## Registry Counts

| Registry | Records | Curated |
| --- | ---: | ---: |
{rows}

## Focus Counts

- Synonym concepts: `{summary['registry_counts']['synonyms']}`
- Synonym canonical/alias/variant forms: `{summary['lexical_form_counts']['synonyms']}`
- Deities: `{summary['registry_counts']['deities']}`
- Deity canonical/alias forms: `{summary['lexical_form_counts']['deities']}`
- Authors: `{summary['registry_counts']['authors']}`
- Author canonical/alias forms: `{summary['lexical_form_counts']['authors']}`
- Motifs: `{summary['registry_counts']['motifs']}`
- Literary devices: `{summary['registry_counts']['literary_devices']}`

## Quality Findings

- IDs and canonical names are unique within each registry.
- Curated aliases do not repeat canonical names or collide within a registry.
- Records are sorted by deterministic ID and have stable content digests.
- Five registries contain three curated seeds each.
- Foundation-only entity, place, work, and theme registries remain unchanged.

## Coverage Limits

- The vocabulary is a small evaluation seed, not a comprehensive Tamil lexicon.
- No lexical source citations or named reviewer sign-offs are attached yet.
- No corpus spans are linked, so occurrence coverage remains zero.
- Contextual ambiguity is unresolved; aliases cannot be expanded blindly.
- Motif and literary-device records are classification targets, not extracted findings.

## Recommended Expansion

Add cited lexical authorities and Tamil researcher review, then create a small manually
annotated corpus sample with positive, negative, and ambiguous examples. Only after that
sample is accepted should entity extraction or query expansion be evaluated.
"""


def write_outputs(
    summary: dict[str, Any],
    *,
    summary_path: Path = DEFAULT_SUMMARY,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_quality_report(summary), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate curated Tamil literary knowledge registries."
    )
    parser.add_argument("--knowledge-dir", type=Path, default=DEFAULT_KNOWLEDGE_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_validation_summary(args.knowledge_dir)
    write_outputs(summary, summary_path=args.summary, report_path=args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
