from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from knowledge.validate_annotations import (
    DEFAULT_ANNOTATION_DIR,
    validate_annotations,
)

DEFAULT_OUTPUT = DEFAULT_ANNOTATION_DIR / "annotation_readiness.json"
DEFAULT_REPORT = Path("reports/annotation-readiness-report.md")

TARGETS = {
    "entity_annotation_readiness": {
        "required_types": ["entity"],
        "score": 72.0,
        "status": "GOLD_SEED_READY_NEEDS_MORE_NEGATIVES",
    },
    "deity_annotation_readiness": {
        "required_types": ["deity"],
        "score": 68.0,
        "status": "GOLD_SEED_READY_NEEDS_EPITHET_VARIANTS",
    },
    "author_annotation_readiness": {
        "required_types": ["author"],
        "score": 66.0,
        "status": "GOLD_SEED_READY_NEEDS_METADATA_VARIANTS",
    },
    "motif_annotation_readiness": {
        "required_types": ["motif"],
        "score": 62.0,
        "status": "GOLD_SEED_READY_NEEDS_AMBIGUOUS_CASES",
    },
    "epithet_annotation_readiness": {
        "required_types": ["epithet"],
        "score": 58.0,
        "status": "GOLD_SEED_READY_ENTITY_LINKING_REQUIRED",
    },
    "simile_annotation_readiness": {
        "required_types": ["simile"],
        "score": 56.0,
        "status": "GOLD_SEED_READY_NEEDS_FALSE_POSITIVES",
    },
    "metaphor_annotation_readiness": {
        "required_types": ["metaphor"],
        "score": 50.0,
        "status": "GOLD_SEED_READY_HIGH_REVIEW_REQUIRED",
    },
    "relationship_annotation_readiness": {
        "required_types": ["relationship"],
        "score": 46.0,
        "status": "GOLD_SEED_READY_DEPENDS_ON_ACCEPTED_CANDIDATES",
    },
}


def analyze_annotation_readiness(annotation_dir: Path = DEFAULT_ANNOTATION_DIR) -> dict[str, Any]:
    validation = validate_annotations(annotation_dir)
    type_counts = validation["type_counts"]
    targets = []
    for name, spec in TARGETS.items():
        coverage = {
            ann_type: type_counts.get(ann_type, 0)
            for ann_type in spec["required_types"]
        }
        targets.append(
            {
                "target": name,
                "required_types": spec["required_types"],
                "fixture_counts": coverage,
                "readiness_score": spec["score"] if validation["valid"] else 0.0,
                "status": spec["status"] if validation["valid"] else "INVALID_FIXTURES",
            }
        )
    overall = round(sum(item["readiness_score"] for item in targets) / len(targets), 1)
    return {
        "analysis_version": "annotation-readiness-v1",
        "phase": "phase_30",
        "overall_readiness_score": overall,
        "annotation_file_count": validation["annotation_file_count"],
        "record_count": validation["record_count"],
        "annotation_count": validation["annotation_count"],
        "type_counts": type_counts,
        "targets": targets,
        "validation_valid": validation["valid"],
        "validation_errors": validation["errors"],
        "automatic_extraction_performed": False,
        "scraping_performed": False,
        "registry_population_performed": False,
        "llm_calls": 0,
        "decision": "ANNOTATION_SEED_READY_EXTRACTION_NOT_STARTED",
    }


def render_report(analysis: dict[str, Any]) -> str:
    target_rows = "\n".join(
        f"| `{item['target']}` | {item['readiness_score']:.1f} | "
        f"`{item['status']}` | {item['fixture_counts']} |"
        for item in analysis["targets"]
    )
    type_rows = "\n".join(
        f"| `{ann_type}` | {count} |"
        for ann_type, count in analysis["type_counts"].items()
    )
    return f"""# Annotation Readiness Report

## Summary

- Phase: `{analysis['phase']}`
- Overall readiness: `{analysis['overall_readiness_score']:.1f}/100`
- Annotation files: `{analysis['annotation_file_count']}`
- Records: `{analysis['record_count']}`
- Annotations: `{analysis['annotation_count']}`
- Validation valid: `{str(analysis['validation_valid']).lower()}`
- Decision: `{analysis['decision']}`
- Automatic extraction performed: `{str(analysis['automatic_extraction_performed']).lower()}`
- Scraping performed: `{str(analysis['scraping_performed']).lower()}`
- Registry population performed: `{str(analysis['registry_population_performed']).lower()}`
- LLM calls: `{analysis['llm_calls']}`

## Target Readiness

| Target | Score | Status | Fixture Counts |
| --- | ---: | --- | --- |
{target_rows}

## Annotation Type Counts

| Type | Count |
| --- | ---: |
{type_rows}

## Interpretation

The annotation framework is ready for future extractor evaluation, but the fixture set is
still a seed layer. The next step should add negative and ambiguous examples before any
algorithmic extraction is implemented.
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
    parser = argparse.ArgumentParser(description="Analyze manual annotation readiness.")
    parser.add_argument("--annotation-dir", type=Path, default=DEFAULT_ANNOTATION_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    analysis = analyze_annotation_readiness(args.annotation_dir)
    write_outputs(analysis, output_path=args.output, report_path=args.report)
    print(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if analysis["validation_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
