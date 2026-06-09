import json

from evaluation.evaluate_retrieval import (
    aggregate_metrics,
    evaluate_query,
    pending_mode,
    reciprocal_rank,
    run_modes,
)


def test_golden_query_loading_shape() -> None:
    query = json.loads(open("data/processed/eval/golden_queries.jsonl", encoding="utf-8").readline())

    assert "query_id" in query
    assert "expected_record_ids" in query
    assert "required_filters" in query


def test_recall_metric_calculation() -> None:
    query = {
        "query_id": "q",
        "query_text": "x",
        "query_type": "test",
        "expected_record_ids": ["r2"],
        "expected_chunk_ids": [],
        "expected_min_results": 1,
    }
    results = [{"record_id": "r1", "chunk_id": "c1"}, {"record_id": "r2", "chunk_id": "c2"}]

    evaluated = evaluate_query(query, results)

    assert evaluated["hit_at_1"] is False
    assert evaluated["hit_at_3"] is True
    assert evaluated["passed"] is True


def test_mrr_calculation() -> None:
    results = [{"record_id": "r1", "chunk_id": "c1"}, {"record_id": "r2", "chunk_id": "c2"}]

    assert reciprocal_rank(results, {"r2"}, set()) == 0.5


def test_aggregate_metrics() -> None:
    query_results = [
        {"hit_at_1": True, "hit_at_3": True, "hit_at_5": True, "hit_at_10": True, "reciprocal_rank": 1.0, "exact_match_at_1": True, "expected_min_results_satisfied": True, "passed": True},
        {"hit_at_1": False, "hit_at_3": True, "hit_at_5": True, "hit_at_10": True, "reciprocal_rank": 0.5, "exact_match_at_1": False, "expected_min_results_satisfied": True, "passed": True},
    ]

    metrics = aggregate_metrics(query_results)

    assert metrics["recall@1"] == 0.5
    assert metrics["MRR"] == 0.75
    assert metrics["failed_queries"] == 0


def test_pending_semantic_mode() -> None:
    result = pending_mode("semantic", 42)

    assert result.status == "PENDING_EMBEDDINGS"
    assert result.metrics["queries_skipped"] == 42


def test_pending_hybrid_mode() -> None:
    result = pending_mode("hybrid", 42, status="PENDING_HYBRID_IMPLEMENTATION")

    assert result.status == "PENDING_HYBRID_IMPLEMENTATION"
    assert result.metrics["queries_skipped"] == 42


def test_deterministic_benchmark_output() -> None:
    queries = [json.loads(line) for line in open("data/processed/eval/golden_queries.jsonl", encoding="utf-8").read().splitlines()[:3]]

    first = run_modes("lexical", queries, top_k=5)
    second = run_modes("lexical", queries, top_k=5)

    assert first == second
