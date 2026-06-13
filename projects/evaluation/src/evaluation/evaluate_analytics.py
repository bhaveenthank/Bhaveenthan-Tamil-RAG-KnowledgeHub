from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    for parent in Path(__file__).resolve().parents:
        shared_src = parent / "shared/tvu-common/src"
        legacy_src = parent / "src"
        if shared_src.is_dir() and legacy_src.is_dir():
            sys.path.insert(0, str(shared_src))
            sys.path.insert(0, str(legacy_src))
            break
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.evaluation_artifacts import write_evaluation_manifest
from evaluation.failure_attribution import attribute_failure, collect_failures, write_outputs as write_failure_outputs
from evaluation.runtime_adapters import retrieve_analytical

DEFAULT_BENCHMARK = Path("data/processed/eval/analytics_benchmark.json")
DEFAULT_OUTPUT = Path("data/processed/eval/analytics_evaluation_results.json")
DEFAULT_REPORT = Path("reports/analytics-evaluation-report.md")
ANALYTICS_OBSERVATIONS_SCHEMA_VERSION = "analytics-observations-v1"


def load_benchmark(path: Path = DEFAULT_BENCHMARK) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def load_observations(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != ANALYTICS_OBSERVATIONS_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported analytics observations schema in {path}: "
            f"{payload.get('schema_version')!r}"
        )
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise ValueError(f"analytics observations must contain an observations list: {path}")
    by_case_id: dict[str, dict[str, Any]] = {}
    for item in observations:
        case_id = item.get("case_id")
        observed = item.get("observed")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"analytics observation is missing case_id: {path}")
        if not isinstance(observed, dict):
            raise ValueError(f"analytics observation {case_id!r} is missing observed payload: {path}")
        by_case_id[case_id] = observed
    return by_case_id


def evaluate_case(
    case: dict[str, Any],
    observations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    observed = (
        observations[case["case_id"]]
        if observations is not None and case["case_id"] in observations
        else retrieve_analytical(case["query"], top_n=case.get("top_n", 10))
    )
    expected = case["expected"]
    checks = {
        "intent": observed.get("intent") == expected.get("intent"),
        "term": observed.get("term") == expected.get("term"),
        "expanded": expected.get("expanded") is None or observed.get("expanded") == expected.get("expanded"),
        "group_by": expected.get("group_by") is None or observed.get("group_by") == expected.get("group_by"),
        "minimum_total": observed.get("total_occurrences", 0) >= expected.get("min_total_occurrences", 0),
        "top_group": not expected.get("top_group_key")
        or bool(observed.get("top_results"))
        and observed["top_results"][0]["group_key"] == expected.get("top_group_key"),
        "matched_terms": set(expected.get("required_matched_terms", [])).issubset(
            set(observed.get("matched_terms", []))
        ),
        "evidence_samples": not expected.get("requires_evidence_samples") or bool(observed.get("evidence_samples")),
    }
    if expected.get("intent") == "unsupported":
        classification = "success" if observed.get("intent") == "unsupported" else "failure"
    elif all(checks.values()):
        classification = "success"
    elif checks["intent"] and checks["term"] and observed.get("total_occurrences", 0) > 0:
        classification = "partial_success"
    else:
        classification = "failure"
    failure = None if classification == "success" else attribute_failure(expected, observed)
    return {
        "case_id": case["case_id"],
        "category": case.get("category", ""),
        "query": case["query"],
        "classification": classification,
        "checks": checks,
        "expected": expected,
        "observed": observed,
        "failure_attribution": failure,
    }


def evaluate_benchmark(
    cases: list[dict[str, Any]],
    observations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if observations is not None:
        missing = sorted(case["case_id"] for case in cases if case["case_id"] not in observations)
        if missing:
            raise ValueError(f"analytics observations missing benchmark cases: {', '.join(missing)}")
    case_results = [evaluate_case(case, observations=observations) for case in cases]
    counts = Counter(item["classification"] for item in case_results)
    category_counts: dict[str, Counter[str]] = {}
    for item in case_results:
        category_counts.setdefault(item["category"], Counter())[item["classification"]] += 1
    total = len(case_results)
    return {
        "analytics_evaluation_version": "analytics-evaluation-v1",
        "benchmark_size": total,
        "summary": {
            "success": counts.get("success", 0),
            "partial_success": counts.get("partial_success", 0),
            "failure": counts.get("failure", 0),
            "success_rate": round(counts.get("success", 0) / total, 4) if total else 0.0,
            "partial_success_rate": round(counts.get("partial_success", 0) / total, 4) if total else 0.0,
            "failure_rate": round(counts.get("failure", 0) / total, 4) if total else 0.0,
        },
        "category_breakdown": {
            category: dict(sorted(counter.items()))
            for category, counter in sorted(category_counts.items())
        },
        "case_results": case_results,
    }


def render_report(results: dict[str, Any]) -> str:
    summary = results["summary"]
    category_rows = "\n".join(
        f"| `{category}` | {values.get('success', 0)} | {values.get('partial_success', 0)} | {values.get('failure', 0)} |"
        for category, values in results["category_breakdown"].items()
    )
    failure_rows = "\n".join(
        f"| `{item['case_id']}` | `{item['classification']}` | `{(item.get('failure_attribution') or {}).get('failure_type', '-')}` |"
        for item in results["case_results"]
        if item["classification"] != "success"
    ) or "| `none` | `success` | `-` |"
    return f"""# Analytics Evaluation Report

## Summary

- Benchmark size: `{results['benchmark_size']}`
- Success rate: `{summary['success_rate'] * 100:.2f}%`
- Partial success rate: `{summary['partial_success_rate'] * 100:.2f}%`
- Failure rate: `{summary['failure_rate'] * 100:.2f}%`
- Successes: `{summary['success']}`
- Partial successes: `{summary['partial_success']}`
- Failures: `{summary['failure']}`

## Category Breakdown

| Category | Success | Partial | Failure |
| --- | ---: | ---: | ---: |
{category_rows}

## Failure Attribution

| Case | Classification | Failure Type |
| --- | --- | --- |
{failure_rows}

## Limitations

- Benchmark expectations are based only on the currently available local corpus.
- The evaluator checks structured analytics, not fluent answer wording.
- No scraping, extraction, LLM calls, GCP work, embedding regeneration, or vector rebuild is performed.
"""


def write_outputs(
    results: dict[str, Any],
    output: Path = DEFAULT_OUTPUT,
    report: Path = DEFAULT_REPORT,
    *,
    manifest_path: Path | None = None,
    source_artifacts: list[str] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(results), encoding="utf-8")
    summary = results["summary"]
    write_evaluation_manifest(
        evaluation_type="analytics",
        producer="evaluation.evaluate_analytics",
        record_count=int(results["benchmark_size"]),
        outputs={"results": output, "report": report},
        manifest_path=manifest_path,
        source_artifacts=source_artifacts or [],
        modes=["analytics"],
        metrics=summary,
        warnings=[
            f"failures:{summary['failure']}"
            for _ in [None]
            if int(summary.get("failure") or 0) > 0
        ],
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate analytical retrieval and analytics components")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument(
        "--observations",
        type=Path,
        help=(
            "Optional analytics observations artifact. When supplied, evaluation scores "
            "the precomputed observed payloads instead of invoking runtime retrieval."
        ),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--manifest", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_artifacts = [str(args.benchmark)]
    observations = None
    if args.observations:
        observations = load_observations(args.observations)
        source_artifacts.append(str(args.observations))
    results = evaluate_benchmark(load_benchmark(args.benchmark), observations=observations)
    write_outputs(
        results,
        args.output,
        args.report,
        manifest_path=args.manifest,
        source_artifacts=source_artifacts,
    )
    failure_results = collect_failures(results)
    write_failure_outputs(failure_results)
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
