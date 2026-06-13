from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_ANALYTICS_RESULTS = Path("data/processed/eval/analytics_evaluation_results.json")
DEFAULT_OUTPUT = Path("data/processed/eval/failure_attribution_results.json")
DEFAULT_REPORT = Path("reports/failure-attribution-report.md")

FAILURE_CATEGORIES = {
    "data_gap": "Expected evidence is not present in the currently available corpus.",
    "parser_gap": "Source evidence may exist, but parser output is not exposing it.",
    "metadata_gap": "Required metadata is missing or inconsistent.",
    "retrieval_gap": "Ranked retrieval missed expected evidence.",
    "query_expansion_gap": "Expansion was expected but not applied correctly.",
    "synonym_gap": "Expected equivalent terms were missing from expansion or matching.",
    "occurrence_gap": "Occurrence search did not find expected evidence rows.",
    "aggregation_gap": "Evidence existed, but grouping/ranking/counting was wrong.",
    "analytics_gap": "Natural-language analytical routing, intent, or term extraction failed.",
    "registry_gap": "Curated registry coverage is insufficient or wrong.",
    "architecture_gap": "The pipeline could not execute the required component path.",
    "evaluation_gap": "The test expectation is underspecified, inconsistent, or stale.",
    "unknown": "The available evidence is insufficient for a stronger attribution.",
}


def attribute_failure(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    if not observed:
        return attribution("architecture_gap", 0.95, "No observed output was produced.", "Inspect CLI/runtime wiring and artifact availability.")

    if expected.get("intent") and observed.get("intent") != expected.get("intent"):
        return attribution(
            "analytics_gap",
            0.92,
            f"Expected intent `{expected.get('intent')}` but observed `{observed.get('intent')}`.",
            "Update deterministic intent rules or benchmark expectation.",
        )
    if expected.get("term") and observed.get("term") != expected.get("term"):
        return attribution(
            "analytics_gap",
            0.90,
            f"Expected term `{expected.get('term')}` but observed `{observed.get('term')}`.",
            "Improve term extraction rules or add a reviewed registry form.",
        )
    if expected.get("expanded") is True and observed.get("expanded") is not True:
        return attribution(
            "query_expansion_gap",
            0.88,
            "Query expansion was expected but not applied.",
            "Check registry matching and expansion decision rules.",
        )
    required_terms = set(expected.get("required_matched_terms", []))
    observed_terms = set(observed.get("matched_terms", []))
    if required_terms and not required_terms.issubset(observed_terms):
        return attribution(
            "synonym_gap",
            0.86,
            f"Missing expected matched terms: {sorted(required_terms - observed_terms)}.",
            "Review curated synonym/alias registry coverage.",
        )
    minimum_total = expected.get("min_total_occurrences")
    if minimum_total is not None and int(observed.get("total_occurrences", 0)) < int(minimum_total):
        failure_type = "data_gap" if int(observed.get("total_occurrences", 0)) == 0 else "occurrence_gap"
        return attribution(
            failure_type,
            0.84,
            f"Expected at least {minimum_total} occurrences but observed {observed.get('total_occurrences', 0)}.",
            "Inspect occurrence index coverage and literal matching rules.",
        )
    expected_top = expected.get("top_group_key")
    observed_top = (observed.get("top_results") or [{}])[0].get("group_key")
    if expected_top and observed_top != expected_top:
        return attribution(
            "aggregation_gap",
            0.82,
            f"Expected top group `{expected_top}` but observed `{observed_top}`.",
            "Inspect grouping metadata and aggregation ranking.",
        )
    expected_group_by = expected.get("group_by")
    if expected_group_by and observed.get("group_by") != expected_group_by:
        return attribution(
            "metadata_gap",
            0.78,
            f"Expected group_by `{expected_group_by}` but observed `{observed.get('group_by')}`.",
            "Check intent-to-group mapping and metadata field availability.",
        )
    if expected.get("requires_evidence_samples") and not observed.get("evidence_samples"):
        return attribution(
            "occurrence_gap",
            0.76,
            "No evidence samples were returned for an evidence-backed query.",
            "Inspect occurrence search result retention and sample projection.",
        )
    return attribution(
        "unknown",
        0.40,
        "No deterministic attribution rule matched the observed mismatch.",
        "Add a more specific attribution rule or enrich benchmark diagnostics.",
    )


def attribution(failure_type: str, confidence: float, explanation: str, recommended_action: str) -> dict[str, Any]:
    return {
        "failure_type": failure_type,
        "confidence": confidence,
        "explanation": explanation,
        "recommended_action": recommended_action,
    }


def collect_failures(evaluation_results: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for item in evaluation_results.get("case_results", []):
        if item.get("classification") == "success":
            continue
        expected = item.get("expected", {})
        observed = item.get("observed", {})
        attributed = item.get("failure_attribution") or attribute_failure(expected, observed)
        failures.append(
            {
                "case_id": item.get("case_id", ""),
                "query": item.get("query", ""),
                "classification": item.get("classification", ""),
                **attributed,
            }
        )
    total_cases = len(evaluation_results.get("case_results", []))
    category_counts = Counter(item["failure_type"] for item in failures)
    return {
        "failure_attribution_version": "failure-attribution-v1",
        "total_cases": total_cases,
        "failure_cases": len(failures),
        "failure_rate": round(len(failures) / total_cases, 4) if total_cases else 0.0,
        "failure_counts": dict(sorted(category_counts.items())),
        "dominant_failure_categories": [
            {"failure_type": key, "count": count}
            for key, count in category_counts.most_common()
        ],
        "failures": failures,
        "taxonomy": FAILURE_CATEGORIES,
    }


def render_report(results: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{item['failure_type']}` | {item['count']} |"
        for item in results["dominant_failure_categories"]
    ) or "| `none` | 0 |"
    recommendations = "\n".join(
        f"- `{item['case_id']}`: {item['recommended_action']}"
        for item in results["failures"][:10]
    ) or "- No failing benchmark cases in the current run."
    return f"""# Failure Attribution Report

## Summary

- Total benchmark cases: `{results['total_cases']}`
- Failure / partial cases: `{results['failure_cases']}`
- Failure rate: `{results['failure_rate'] * 100:.2f}%`

## Failure Counts

| Failure Type | Count |
| --- | ---: |
{rows}

## Recommendations

{recommendations}

## Taxonomy

The full deterministic taxonomy is documented in `docs/failure-taxonomy.md`.
"""


def write_outputs(results: dict[str, Any], output: Path = DEFAULT_OUTPUT, report: Path = DEFAULT_REPORT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(results), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize deterministic failure attribution results")
    parser.add_argument("--analytics-results", type=Path, default=DEFAULT_ANALYTICS_RESULTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    evaluation_results = json.loads(args.analytics_results.read_text(encoding="utf-8"))
    results = collect_failures(evaluation_results)
    write_outputs(results, args.output, args.report)
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
