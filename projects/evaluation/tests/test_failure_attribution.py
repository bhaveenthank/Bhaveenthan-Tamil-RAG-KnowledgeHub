import json
from pathlib import Path

import pytest

from evaluation.evaluate_analytics import evaluate_benchmark, load_observations, render_report, write_outputs
from evaluation.failure_attribution import attribute_failure, collect_failures, render_report as render_failure_report


def test_failure_classification_and_confidence() -> None:
    result = attribute_failure(
        {"intent": "group_by_author", "term": "சந்திரன்"},
        {"intent": "group_by_category", "term": "சந்திரன்"},
    )

    assert result["failure_type"] == "analytics_gap"
    assert result["confidence"] >= 0.9
    assert result["recommended_action"]


def test_synonym_gap_classification() -> None:
    result = attribute_failure(
        {"required_matched_terms": ["சந்திரன்", "நிலா"]},
        {"matched_terms": ["சந்திரன்"]},
    )

    assert result["failure_type"] == "synonym_gap"
    assert result["confidence"] >= 0.8


def test_benchmark_evaluation_runs_and_is_deterministic() -> None:
    cases = [
        {
            "case_id": "author_moon",
            "category": "author-analysis",
            "query": "எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?",
            "expected": {
                "intent": "group_by_author",
                "term": "சந்திரன்",
                "expanded": True,
                "group_by": "author",
                "min_total_occurrences": 686,
                "top_group_key": "Tirugnanasambandar",
                "required_matched_terms": ["சந்திரன்", "நிலா", "மதி", "திங்கள்", "நிலவு"],
                "requires_evidence_samples": True,
            },
        },
        {
            "case_id": "unsupported",
            "category": "unsupported",
            "query": "hello please summarize everything",
            "expected": {
                "intent": "unsupported",
                "term": "",
                "expanded": False,
                "group_by": None,
                "min_total_occurrences": 0,
                "requires_evidence_samples": False,
            },
        },
    ]
    first = evaluate_benchmark(cases)
    second = evaluate_benchmark(cases)

    assert first == second
    assert first["benchmark_size"] == 2
    assert first["summary"]["success"] == 2
    assert first["summary"]["failure"] == 0
    assert "Analytics Evaluation Report" in render_report(first)


def test_benchmark_can_replay_observation_artifact(tmp_path) -> None:
    observations_path = tmp_path / "analytics-observations.json"
    observations_path.write_text(
        json.dumps(
            {
                "schema_version": "analytics-observations-v1",
                "producer": "retrieval.analytics_fixture",
                "observations": [
                    {
                        "case_id": "author_moon",
                        "observed": {
                            "intent": "group_by_author",
                            "term": "சந்திரன்",
                            "expanded": True,
                            "group_by": "author",
                            "total_occurrences": 700,
                            "top_results": [{"group_key": "Tirugnanasambandar"}],
                            "matched_terms": ["சந்திரன்", "நிலா"],
                            "evidence_samples": [{"record_id": "r1"}],
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    cases = [
        {
            "case_id": "author_moon",
            "category": "author-analysis",
            "query": "எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?",
            "expected": {
                "intent": "group_by_author",
                "term": "சந்திரன்",
                "expanded": True,
                "group_by": "author",
                "min_total_occurrences": 686,
                "top_group_key": "Tirugnanasambandar",
                "required_matched_terms": ["சந்திரன்", "நிலா"],
                "requires_evidence_samples": True,
            },
        }
    ]

    results = evaluate_benchmark(cases, observations=load_observations(observations_path))

    assert results["summary"]["success"] == 1
    assert results["case_results"][0]["observed"]["total_occurrences"] == 700


def test_observation_artifact_must_cover_benchmark_cases() -> None:
    cases = [
        {
            "case_id": "missing",
            "category": "author-analysis",
            "query": "q",
            "expected": {"intent": "unsupported", "term": ""},
        }
    ]

    with pytest.raises(ValueError, match="missing benchmark cases: missing"):
        evaluate_benchmark(cases, observations={})


def test_analytics_outputs_write_manifest(tmp_path) -> None:
    results = {
        "analytics_evaluation_version": "analytics-evaluation-v1",
        "benchmark_size": 2,
        "summary": {
            "success": 1,
            "partial_success": 0,
            "failure": 1,
            "success_rate": 0.5,
            "partial_success_rate": 0.0,
            "failure_rate": 0.5,
        },
        "category_breakdown": {"test": {"success": 1, "failure": 1}},
        "case_results": [
            {"case_id": "ok", "classification": "success"},
            {
                "case_id": "bad",
                "classification": "failure",
                "failure_attribution": {"failure_type": "analytics_gap"},
            },
        ],
    }
    output = tmp_path / "analytics.json"
    report = tmp_path / "analytics.md"
    manifest_path = tmp_path / "manifest.json"

    write_outputs(
        results,
        output,
        report,
        manifest_path=manifest_path,
        source_artifacts=["analytics_benchmark.json"],
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["artifact_type"] == "evaluation_result"
    assert manifest["evaluation_type"] == "analytics"
    assert manifest["source_artifacts"] == ["analytics_benchmark.json"]
    assert manifest["record_count"] == 2
    assert manifest["warnings"] == ["failures:1"]
    assert set(manifest["checksums"]) == {"results", "report"}


def test_failure_collection_and_report_generation() -> None:
    results = {
        "case_results": [
            {
                "case_id": "bad_top",
                "query": "q",
                "classification": "failure",
                "expected": {"top_group_key": "A"},
                "observed": {"top_results": [{"group_key": "B"}]},
            }
        ]
    }
    failures = collect_failures(results)
    report = render_failure_report(failures)

    assert failures["failure_cases"] == 1
    assert failures["failure_counts"]["aggregation_gap"] == 1
    assert "Failure Attribution Report" in report


def test_no_scraping_or_llm_dependencies() -> None:
    text = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in (
            "src/evaluation/failure_attribution.py",
            "src/evaluation/evaluate_analytics.py",
        )
    )

    for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
        assert forbidden not in text
