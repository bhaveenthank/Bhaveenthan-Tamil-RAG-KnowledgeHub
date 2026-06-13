from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_EXTRACTION_DIR = Path("data/knowledge/extraction")
DEFAULT_OUTPUT = DEFAULT_EXTRACTION_DIR / "extraction_readiness.json"
DEFAULT_REPORT = Path("reports/extraction-readiness-report.md")
DEFAULT_ENTITY_EVAL = Path("data/processed/eval/entity_extraction_results.json")

TARGETS: dict[str, dict[str, Any]] = {
    "entity_extraction": {
        "candidate_file": "entities_candidates.json",
        "readiness_score": 55.0,
        "status": "FRAMEWORK_READY_REQUIRES_ANNOTATED_FIXTURES",
        "blockers": ["needs reviewed entity examples", "needs ambiguity rules"],
    },
    "deity_extraction": {
        "candidate_file": "entities_candidates.json",
        "readiness_score": 52.0,
        "status": "FRAMEWORK_READY_REQUIRES_ALIAS_REVIEW",
        "blockers": ["needs deity epithet mapping", "needs false-positive examples"],
    },
    "author_extraction": {
        "candidate_file": "entities_candidates.json",
        "readiness_score": 52.0,
        "status": "FRAMEWORK_READY_REQUIRES_METADATA_ALIGNMENT",
        "blockers": ["needs author authority review", "needs work-attribution checks"],
    },
    "motif_extraction": {
        "candidate_file": "motif_candidates.json",
        "readiness_score": 45.0,
        "status": "SCHEMA_READY_EXTRACTION_RULES_NOT_STARTED",
        "blockers": ["needs motif annotation guidelines", "needs negative examples"],
    },
    "epithet_extraction": {
        "candidate_file": "epithet_candidates.json",
        "readiness_score": 40.0,
        "status": "SCHEMA_READY_ENTITY_LINKING_REQUIRED",
        "blockers": ["needs entity linking", "needs reviewed epithet inventory"],
    },
    "simile_extraction": {
        "candidate_file": "simile_candidates.json",
        "readiness_score": 38.0,
        "status": "SCHEMA_READY_MARKER_RULES_REQUIRED",
        "blockers": ["needs marker list", "needs subject-object parsing"],
    },
    "metaphor_extraction": {
        "candidate_file": "metaphor_candidates.json",
        "readiness_score": 36.0,
        "status": "SCHEMA_READY_HIGH_REVIEW_REQUIRED",
        "blockers": ["needs interpretation guidelines", "needs human review workflow"],
    },
    "relationship_extraction": {
        "candidate_file": "relationship_candidates.json",
        "readiness_score": 34.0,
        "status": "SCHEMA_READY_DEPENDS_ON_OTHER_TARGETS",
        "blockers": ["depends on accepted candidates", "needs relationship ontology"],
    },
}

REQUIRED_DOCS = [
    Path("docs/literary-knowledge-extraction-framework.md"),
    Path("docs/knowledge-target-catalog.md"),
    Path("docs/extraction-schemas.md"),
]

PLACEHOLDER_CANDIDATE_FILES = [
    "entities_candidates.json",
    "motif_candidates.json",
    "theme_candidates.json",
    "epithet_candidates.json",
    "simile_candidates.json",
    "metaphor_candidates.json",
    "relationship_candidates.json",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def validate_candidate_store(path: Path, expected_name: str) -> dict[str, Any]:
    payload = load_json(path)
    records = payload.get("records", []) if isinstance(payload.get("records"), list) else []
    errors: list[str] = []
    if not path.exists():
        errors.append("candidate store is missing")
    if payload.get("registry_name") != expected_name:
        errors.append("registry_name mismatch")
    if payload.get("schema_version") != "extraction-candidate-v1":
        errors.append("schema_version mismatch")
    if payload.get("status") != "framework_placeholder_only":
        errors.append("candidate store must remain framework_placeholder_only")
    if payload.get("automatic_extraction_performed") is not False:
        errors.append("automatic_extraction_performed must be false")
    if not records:
        errors.append("candidate store should include one placeholder shape example")
    for record in records:
        if record.get("status") != "placeholder_seed":
            errors.append("placeholder records must use status placeholder_seed")
        if float(record.get("confidence", -1)) != 0.0:
            errors.append("placeholder records must use confidence 0.0")
        if record.get("source_record_id") != "placeholder_only":
            errors.append("placeholder records must not claim corpus evidence")
    return {
        "path": str(path),
        "exists": path.exists(),
        "record_count": len(records),
        "errors": sorted(set(errors)),
        "automatic_extraction_performed": payload.get("automatic_extraction_performed", None),
    }


def analyze_extraction_readiness(
    extraction_dir: Path = DEFAULT_EXTRACTION_DIR,
    required_docs: list[Path] | None = None,
    entity_eval_path: Path = DEFAULT_ENTITY_EVAL,
) -> dict[str, Any]:
    docs = required_docs or REQUIRED_DOCS
    doc_status = {str(path): path.exists() for path in docs}
    entity_eval = load_json(entity_eval_path)
    target_results = []
    unique_files = sorted(set(PLACEHOLDER_CANDIDATE_FILES))
    store_validation = {
        file_name: validate_candidate_store(
            extraction_dir / file_name,
            Path(file_name).stem,
        )
        for file_name in unique_files
    }
    for target, config in TARGETS.items():
        store = store_validation[config["candidate_file"]]
        readiness_score = config["readiness_score"]
        status = config["status"]
        blockers = list(config["blockers"])
        if target == "entity_extraction" and entity_eval:
            readiness_score = round(55.0 + float(entity_eval.get("f1", 0.0)) * 25.0, 1)
            status = "PILOT_EVALUATED_DETERMINISTIC_MATCHER"
            blockers = [
                "needs broader negative and ambiguous fixtures",
                "needs missing authority review before registry expansion",
            ]
        target_results.append(
            {
                "target": target,
                "candidate_file": config["candidate_file"],
                "schema_defined": all(doc_status.values()),
                "candidate_store_exists": store["exists"],
                "candidate_store_errors": store["errors"],
                "readiness_score": readiness_score,
                "status": status,
                "blockers": blockers,
                "automatic_extraction_performed": False,
                "scraping_performed": False,
                "llm_calls": 0,
            }
        )
    overall = round(
        sum(item["readiness_score"] for item in target_results) / len(target_results),
        1,
    )
    return {
        "analysis_version": "literary-knowledge-extraction-framework-v1",
        "phase": "phase_29",
        "framework_status": "FRAMEWORK_READY_POPULATION_NOT_STARTED",
        "overall_readiness_score": overall,
        "target_count": len(target_results),
        "targets": target_results,
        "candidate_store_validation": store_validation,
        "required_docs": doc_status,
        "entity_extraction_pilot": {
            "available": bool(entity_eval),
            "precision": entity_eval.get("precision", 0.0),
            "recall": entity_eval.get("recall", 0.0),
            "f1": entity_eval.get("f1", 0.0),
            "corpus_wide_extraction_performed": entity_eval.get(
                "corpus_wide_extraction_performed",
                False,
            ),
        },
        "automatic_extraction_performed": False,
        "scraping_performed": False,
        "registry_population_performed": False,
        "llm_calls": 0,
        "next_recommended_phase": (
            "deity and author extraction pilot"
            if entity_eval
            else "controlled annotated fixture design"
        ),
    }


def render_report(analysis: dict[str, Any]) -> str:
    target_rows = "\n".join(
        "| `{target}` | `{candidate}` | {score:.1f} | `{status}` | {blockers} |".format(
            target=item["target"],
            candidate=item["candidate_file"],
            score=item["readiness_score"],
            status=item["status"],
            blockers=", ".join(item["blockers"]),
        )
        for item in analysis["targets"]
    )
    store_rows = "\n".join(
        f"| `{name}` | `{details['exists']}` | {details['record_count']} | "
        f"{'; '.join(details['errors']) or 'none'} |"
        for name, details in analysis["candidate_store_validation"].items()
    )
    return f"""# Extraction Readiness Report

## Summary

- Phase: `{analysis['phase']}`
- Framework status: `{analysis['framework_status']}`
- Extraction targets: `{analysis['target_count']}`
- Overall readiness: `{analysis['overall_readiness_score']:.1f}/100`
- Automatic extraction performed: `{str(analysis['automatic_extraction_performed']).lower()}`
- Scraping performed: `{str(analysis['scraping_performed']).lower()}`
- Registry population performed: `{str(analysis['registry_population_performed']).lower()}`
- LLM calls: `{analysis['llm_calls']}`
- Next recommended phase: `{analysis['next_recommended_phase']}`
- Entity extraction pilot available: `{str(analysis['entity_extraction_pilot']['available']).lower()}`
- Entity extraction pilot F1: `{analysis['entity_extraction_pilot']['f1']}`

## Target Readiness

| Target | Candidate Store | Score | Status | Main Blockers |
| --- | --- | ---: | --- | --- |
{target_rows}

## Candidate Store Validation

| Store | Exists | Placeholder Records | Errors |
| --- | --- | ---: | --- |
{store_rows}

## Interpretation

The framework is ready for controlled annotation design, but not for automatic extraction
or registry promotion. The lowest-readiness targets are relationship, metaphor, and simile
extraction because they require accepted lower-level candidates, rhetorical interpretation
rules, and human review.
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
        description="Analyze readiness for future Tamil literary knowledge extraction."
    )
    parser.add_argument("--extraction-dir", type=Path, default=DEFAULT_EXTRACTION_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--entity-eval", type=Path, default=DEFAULT_ENTITY_EVAL)
    args = parser.parse_args(argv)
    analysis = analyze_extraction_readiness(args.extraction_dir, entity_eval_path=args.entity_eval)
    write_outputs(analysis, output_path=args.output, report_path=args.report)
    print(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True))
    has_errors = any(
        details["errors"]
        for details in analysis["candidate_store_validation"].values()
    )
    missing_docs = not all(analysis["required_docs"].values())
    return 1 if has_errors or missing_docs else 0


if __name__ == "__main__":
    raise SystemExit(main())
