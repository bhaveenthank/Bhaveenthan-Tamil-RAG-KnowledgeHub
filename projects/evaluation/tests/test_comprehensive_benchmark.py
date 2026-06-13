import json
from pathlib import Path

from evaluation.run_comprehensive_benchmark import (
    benchmark_category,
    render_report,
    render_unlock_roadmap,
    run_benchmark,
    summarize_results,
    write_outputs,
)


def test_benchmark_execution_and_category_evaluation() -> None:
    payload = run_benchmark()

    assert payload["question_count"] == 100
    assert payload["summary"]["overall"]["total_questions"] == 100
    assert "ordinary retrieval" in payload["summary"]["category_counts"]
    assert payload["summary"]["overall"]["success"] > 0
    assert payload["summary"]["overall"]["failure"] > 0


def test_failure_attribution_integration() -> None:
    payload = run_benchmark()
    failures = [item for item in payload["results"] if item["status"] == "failure"]

    assert failures
    assert all(item["failure_attribution"] for item in failures)
    assert {"data_gap", "architecture_gap", "registry_gap"} & {
        item["failure_type"] for item in failures
    }


def test_report_generation_and_determinism() -> None:
    results = [
        {
            "status": "success",
            "category": "ordinary retrieval",
            "failure_type": "",
            "question_id": "q_001",
            "question": "q",
        },
        {
            "status": "failure",
            "category": "unsupported questions",
            "failure_type": "architecture_gap",
            "question_id": "q_002",
            "question": "q2",
        },
    ]
    first = {
        "summary": summarize_results(results),
        "results": results,
    }
    second = {
        "summary": summarize_results(results),
        "results": results,
    }
    report = render_report(first)
    roadmap = render_unlock_roadmap(results)

    assert first == second
    assert "Comprehensive Benchmark Report" in report
    assert "Top Failure Causes" in report
    assert "Question Unlock Roadmap" in roadmap


def test_question_category_mapping() -> None:
    question = {
        "category": "H. Cross-hymn and cross-corpus",
        "question_tamil": "தேவாரத்திலும் திருப்புகழிலும் ஒப்பிடுக",
        "requires": {"cross_corpus": True, "llm_generation": False},
    }

    assert benchmark_category(question) == "cross-corpus questions"


def test_summary_shape() -> None:
    results = [
        {"status": "success", "category": "ordinary retrieval", "failure_type": ""},
        {"status": "partial", "category": "aggregation questions", "failure_type": "aggregation_gap"},
        {"status": "failure", "category": "unsupported questions", "failure_type": "architecture_gap"},
    ]
    summary = summarize_results(results)

    assert summary["overall"]["success_rate"] == 0.3333
    assert summary["failure_counts"]["architecture_gap"] == 1
    assert summary["failure_counts"]["aggregation_gap"] == 1


def test_comprehensive_outputs_write_manifest(tmp_path) -> None:
    results = [
        {
            "status": "success",
            "category": "ordinary retrieval",
            "failure_type": "",
            "question_id": "q_001",
            "question": "q",
        },
        {
            "status": "failure",
            "category": "unsupported questions",
            "failure_type": "architecture_gap",
            "question_id": "q_002",
            "question": "q2",
        },
    ]
    payload = {
        "benchmark_version": "comprehensive-benchmark-v1",
        "source_taxonomy": "taxonomy.jsonl",
        "question_count": len(results),
        "results": results,
        "summary": summarize_results(results),
    }
    output = tmp_path / "benchmark.json"
    summary = tmp_path / "summary.json"
    report = tmp_path / "report.md"
    capability = tmp_path / "capability.md"
    roadmap = tmp_path / "roadmap.md"
    manifest_path = tmp_path / "manifest.json"

    write_outputs(
        payload,
        output,
        summary,
        report,
        capability,
        roadmap,
        manifest_path=manifest_path,
        source_artifacts=["taxonomy.jsonl"],
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["artifact_type"] == "evaluation_result"
    assert manifest["evaluation_type"] == "comprehensive_benchmark"
    assert manifest["record_count"] == 2
    assert manifest["source_artifacts"] == ["taxonomy.jsonl"]
    assert set(manifest["checksums"]) == {
        "capability_report",
        "report",
        "results",
        "roadmap",
        "summary",
    }
    assert manifest["warnings"] == ["failures:1"]


def test_no_scraping_or_llm_dependencies() -> None:
    text = Path("src/evaluation/run_comprehensive_benchmark.py").read_text(encoding="utf-8").lower()

    for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
        assert forbidden not in text
