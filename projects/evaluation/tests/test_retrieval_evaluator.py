import json

from evaluation import evaluate_retrieval
from evaluation.evaluate_retrieval import (
    aggregate_metrics,
    evaluate_query,
    pending_mode,
    reciprocal_rank,
    run_modes,
    write_outputs,
)
from evaluation.evaluate_query_expansion import (
    evaluate as evaluate_query_expansion,
    render_report as render_query_expansion_report,
    write_outputs as write_query_expansion_outputs,
)
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.query_expander import QueryExpander


class FakeSemanticRetriever:
    def search(self, query_text: str, filters=None, top_k: int = 10) -> list[dict]:
        return [
            {
                "rank": 1,
                "score": 0.9,
                "similarity_score": 0.9,
                "retrieval_mode": "semantic",
                "record_id": "r1",
                "parent_record_id": "r1",
                "chunk_id": "c1",
                "chunk_type": "verse_plus_commentary",
                "citation_text": "TamilVU citation",
                "source_urls": {"hymn_url": "https://www.tamilvu.org/"},
                "deterministic_rank_key": "001",
            }
        ][:top_k]


class FakeLexicalRetriever:
    def search(self, query_text: str, filters=None, top_k: int = 10) -> list[dict]:
        return [
            {
                "rank": 1,
                "score": 100.0,
                "retrieval_mode": "lexical",
                "record_id": "r1",
                "chunk_id": "c1-lex",
                "chunk_type": "verse_only",
                "matched_fields": [
                    "exact_song_no",
                    "metadata_filter:song_no",
                    "verse_text_normalized",
                ],
                "citation_text": "Lexical citation",
                "source_urls": {"hymn_url": "https://www.tamilvu.org/r1"},
                "deterministic_rank_key": "001",
            }
        ][:top_k]


class FakeExpansionRetriever:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, filters=None, top_k: int = 5) -> list[dict]:
        self.queries.append(query)
        record_id = "r2" if "திருநாவுக்கரசர்" in query else "r1"
        return [
            {
                "rank": 1,
                "record_id": record_id,
                "parent_record_id": record_id,
                "chunk_id": f"{record_id}_verse_plus_commentary",
                "chunk_type": "verse_plus_commentary",
                "matched_modes": ["lexical"],
                "hybrid_score": 1.0,
                "citation_text": record_id,
                "source_urls": {},
                "deterministic_rank_key": record_id,
            }
        ][:top_k]


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


def test_evaluator_semantic_mode(monkeypatch, tmp_path) -> None:
    vector_manifest = tmp_path / "vector_index_manifest.json"
    vector_manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(evaluate_retrieval, "DEFAULT_VECTOR_MANIFEST", vector_manifest)
    monkeypatch.setattr(evaluate_retrieval, "SemanticRetriever", lambda: FakeSemanticRetriever())
    queries = [
        {
            "query_id": "q1",
            "query_text": "அருள்",
            "query_type": "semantic",
            "expected_record_ids": ["r1"],
            "expected_chunk_ids": [],
            "expected_min_results": 1,
            "required_filters": {},
        }
    ]

    results = evaluate_retrieval.run_modes("semantic", queries)

    assert results["semantic"]["status"] == "EVALUATED"
    assert results["semantic"]["metrics"]["recall@1"] == 1.0


def test_evaluator_semantic_pending_when_index_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(evaluate_retrieval, "DEFAULT_VECTOR_MANIFEST", tmp_path / "missing.json")

    results = evaluate_retrieval.run_modes("semantic", [])

    assert results["semantic"]["status"] == "PENDING_VECTOR_INDEX"


def test_evaluator_hybrid_mode(monkeypatch, tmp_path) -> None:
    vector_manifest = tmp_path / "vector_index_manifest.json"
    vector_manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(evaluate_retrieval, "DEFAULT_VECTOR_MANIFEST", vector_manifest)
    monkeypatch.setattr(
        evaluate_retrieval,
        "HybridRetriever",
        lambda lexical_weight=0.65, semantic_weight=0.35: HybridRetriever(
            FakeLexicalRetriever(),
            FakeSemanticRetriever(),
        ),
    )
    queries = [
        {
            "query_id": "q1",
            "query_text": "song",
            "query_type": "test",
            "expected_record_ids": ["r1"],
            "expected_chunk_ids": [],
            "expected_min_results": 1,
            "required_filters": {"song_no": "1"},
        }
    ]

    results = evaluate_retrieval.run_modes("hybrid", queries, include_ablations=False)

    assert results["hybrid"]["status"] == "EVALUATED"
    assert results["hybrid"]["metrics"]["recall@1"] == 1.0


def test_comparison_report_generation() -> None:
    results = {
        "lexical": evaluate_retrieval.mode_to_dict(evaluate_retrieval.pending_mode("lexical", 0)),
        "semantic": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode("semantic", 0, status="EVALUATED")
        ),
        "hybrid": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode(
                "hybrid",
                0,
                status="PENDING_HYBRID_IMPLEMENTATION",
            )
        ),
    }

    report = evaluate_retrieval.render_comparison_report(results)

    assert "lexical" in report
    assert "semantic" in report
    assert "PENDING_HYBRID_IMPLEMENTATION" in report


def test_comparison_report_includes_hybrid_metrics() -> None:
    results = {
        "lexical": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode("lexical", 0, status="EVALUATED")
        ),
        "semantic": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode("semantic", 0, status="EVALUATED")
        ),
        "hybrid": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode("hybrid", 0, status="EVALUATED")
        ),
    }

    report = evaluate_retrieval.render_comparison_report(results)

    assert "Hybrid improved over semantic" in report
    assert "Hybrid matched lexical" in report


def test_ablation_runs(monkeypatch, tmp_path) -> None:
    vector_manifest = tmp_path / "vector_index_manifest.json"
    vector_manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(evaluate_retrieval, "DEFAULT_VECTOR_MANIFEST", vector_manifest)
    monkeypatch.setattr(
        evaluate_retrieval,
        "HybridRetriever",
        lambda lexical_weight=0.65, semantic_weight=0.35: HybridRetriever(
            FakeLexicalRetriever(),
            FakeSemanticRetriever(),
        ),
    )
    queries = [
        {
            "query_id": "q1",
            "query_text": "song",
            "query_type": "test",
            "expected_record_ids": ["r1"],
            "expected_chunk_ids": [],
            "expected_min_results": 1,
            "required_filters": {},
        }
    ]

    ablations = evaluate_retrieval.run_hybrid_ablations(queries)

    assert set(ablations) == {"lexical-heavy", "balanced", "semantic-heavy"}


def test_query_expansion_evaluation_and_report_generation(tmp_path) -> None:
    records = {
        "r1": {"record_id": "r1", "verse_text_normalized": "பொதுப் பாடல்"},
        "r2": {"record_id": "r2", "verse_text_normalized": "திருநாவுக்கரசர் பாடல்"},
    }
    cases = ({"query_id": "author", "query": "அப்பர் பாடல்கள்"},)

    first = evaluate_query_expansion(
        FakeExpansionRetriever(),
        QueryExpander(),
        records,
        cases=cases,
        top_k=1,
    )
    second = evaluate_query_expansion(
        FakeExpansionRetriever(),
        QueryExpander(),
        records,
        cases=cases,
        top_k=1,
    )
    output = tmp_path / "results.json"
    report = tmp_path / "report.md"
    manifest_path = tmp_path / "query-expansion.manifest.json"
    write_query_expansion_outputs(
        first,
        output,
        report,
        manifest_path=manifest_path,
        source_artifacts=["enriched.jsonl"],
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert first == second
    assert first["summary"]["improved"] == 1
    assert json.loads(output.read_text(encoding="utf-8"))["summary"]["queries_tested"] == 1
    assert "Query Results" in render_query_expansion_report(first)
    assert report.exists()
    assert manifest["artifact_type"] == "evaluation_result"
    assert manifest["evaluation_type"] == "query_expansion"
    assert manifest["source_artifacts"] == ["enriched.jsonl"]
    assert manifest["record_count"] == 1
    assert set(manifest["checksums"]) == {"results", "report"}


def test_retrieval_outputs_write_manifest(tmp_path) -> None:
    results = {
        "lexical": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode("lexical", 0, status="EVALUATED")
        ),
        "semantic": evaluate_retrieval.mode_to_dict(
            evaluate_retrieval.pending_mode("semantic", 2, status="PENDING_VECTOR_INDEX")
        ),
    }
    results_path = tmp_path / "retrieval_results.json"
    report_path = tmp_path / "retrieval.md"
    semantic_report_path = tmp_path / "semantic.md"
    hybrid_report_path = tmp_path / "hybrid.md"
    comparison_path = tmp_path / "comparison.md"
    manifest_path = tmp_path / "manifest.json"

    write_outputs(
        results,
        results_path,
        report_path,
        semantic_report_path,
        hybrid_report_path,
        comparison_path,
        manifest_path=manifest_path,
        source_artifacts=["golden.jsonl"],
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["artifact_type"] == "evaluation_result"
    assert manifest["schema_version"] == "evaluation-result-v1"
    assert manifest["evaluation_type"] == "retrieval_benchmark"
    assert manifest["source_artifacts"] == ["golden.jsonl"]
    assert set(manifest["checksums"]) == {
        "comparison_report",
        "hybrid_report",
        "report",
        "results",
        "semantic_report",
    }
    assert manifest["warnings"] == ["semantic:PENDING_VECTOR_INDEX"]
