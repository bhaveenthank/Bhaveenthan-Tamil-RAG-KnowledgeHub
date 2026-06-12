from pathlib import Path

from evaluation.evaluate_analytics import evaluate_benchmark, render_report
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
