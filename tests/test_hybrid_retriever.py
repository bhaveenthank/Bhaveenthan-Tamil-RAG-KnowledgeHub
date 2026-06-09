from evaluation import evaluate_retrieval
from retrieval.hybrid_retriever import (
    HybridCandidate,
    HybridRetriever,
    exact_match_boost,
    hybrid_score,
    merge_candidates,
    metadata_filter_boost,
)


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
                "matched_fields": ["exact_song_no", "metadata_filter:song_no", "verse_text_normalized"],
                "citation_text": "Lexical citation",
                "source_urls": {"hymn_url": "https://www.tamilvu.org/r1"},
                "deterministic_rank_key": "001",
            },
            {
                "rank": 2,
                "score": 50.0,
                "retrieval_mode": "lexical",
                "record_id": "r2",
                "chunk_id": "c2-lex",
                "chunk_type": "verse_only",
                "matched_fields": ["pozhppurai_normalized"],
                "citation_text": "Lexical citation 2",
                "source_urls": {"hymn_url": "https://www.tamilvu.org/r2"},
                "deterministic_rank_key": "002",
            },
        ][:top_k]


class FakeSemanticRetriever:
    def search(self, query_text: str, filters=None, top_k: int = 10) -> list[dict]:
        return [
            {
                "rank": 1,
                "score": 0.95,
                "similarity_score": 0.95,
                "retrieval_mode": "semantic",
                "record_id": "r3",
                "parent_record_id": "r3",
                "chunk_id": "c3-sem",
                "chunk_type": "verse_plus_commentary",
                "citation_text": "Semantic citation 3",
                "source_urls": {"hymn_url": "https://www.tamilvu.org/r3"},
                "deterministic_rank_key": "003",
            },
            {
                "rank": 2,
                "score": 0.90,
                "similarity_score": 0.90,
                "retrieval_mode": "semantic",
                "record_id": "r1",
                "parent_record_id": "r1",
                "chunk_id": "c1-sem",
                "chunk_type": "verse_plus_commentary",
                "citation_text": "Semantic citation 1",
                "source_urls": {"hymn_url": "https://www.tamilvu.org/r1"},
                "deterministic_rank_key": "001",
            },
        ][:top_k]


def test_hybrid_result_merging_and_deduplication() -> None:
    lexical = FakeLexicalRetriever().search("song")
    semantic = FakeSemanticRetriever().search("song")

    merged = merge_candidates(lexical, semantic)

    assert set(merged) == {"r1", "r2", "r3"}
    assert merged["r1"].matched_modes == {"lexical", "semantic"}
    assert merged["r1"].chunk_id == "c1-lex"


def test_matched_modes_field() -> None:
    retriever = HybridRetriever(FakeLexicalRetriever(), FakeSemanticRetriever())

    results = retriever.search("song", filters={"song_no": "1"}, top_k=3)

    assert results[0]["matched_modes"] == ["both"]
    assert any(result["matched_modes"] == ["semantic"] for result in results)


def test_hybrid_score_calculation() -> None:
    candidate = HybridCandidate(
        record_id="r1",
        chunk_id="c1",
        chunk_type="verse_only",
        citation_text="citation",
        source_urls={},
        deterministic_rank_key="001",
        normalized_lexical_score=1.0,
        normalized_semantic_score=0.5,
        matched_fields={"exact_song_no"},
    )

    score, exact_boost, metadata_boost = hybrid_score(candidate, "query", {}, 0.65, 0.35)

    assert score == 1.075
    assert exact_boost == 0.25
    assert metadata_boost == 0.0


def test_deterministic_tie_breaking() -> None:
    class TieLexical:
        def search(self, query_text: str, filters=None, top_k: int = 10) -> list[dict]:
            return [
                {
                    "score": 1,
                    "record_id": "r2",
                    "chunk_id": "c2",
                    "chunk_type": "verse_only",
                    "matched_fields": [],
                    "citation_text": "c2",
                    "source_urls": {},
                    "deterministic_rank_key": "002",
                },
                {
                    "score": 1,
                    "record_id": "r1",
                    "chunk_id": "c1",
                    "chunk_type": "verse_only",
                    "matched_fields": [],
                    "citation_text": "c1",
                    "source_urls": {},
                    "deterministic_rank_key": "001",
                },
            ]

    class EmptySemantic:
        def search(self, query_text: str, filters=None, top_k: int = 10) -> list[dict]:
            return []

    results = HybridRetriever(TieLexical(), EmptySemantic()).search("x", top_k=2)

    assert [result["record_id"] for result in results] == ["r1", "r2"]


def test_exact_match_boosts() -> None:
    candidate = HybridCandidate(
        record_id="thevaram_02_1664_1470",
        chunk_id="thevaram_02_1664_1470_verse_only",
        chunk_type="verse_only",
        citation_text="citation",
        source_urls={},
        deterministic_rank_key="001",
        matched_fields={"exact_record_id", "verse_text_normalized"},
    )

    boost = exact_match_boost("thevaram_02_1664_1470", {"hymn_id": "1664"}, candidate)

    assert boost > 0.4


def test_metadata_boosts() -> None:
    candidate = HybridCandidate(
        record_id="r1",
        chunk_id="c1",
        chunk_type="verse_only",
        citation_text="citation",
        source_urls={},
        deterministic_rank_key="001",
        matched_fields={"metadata_filter:hymn_id"},
    )

    assert metadata_filter_boost({"hymn_id": "1664"}, candidate) == 0.05


def test_evaluator_hybrid_mode(monkeypatch, tmp_path) -> None:
    vector_manifest = tmp_path / "vector_index_manifest.json"
    vector_manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(evaluate_retrieval, "DEFAULT_VECTOR_MANIFEST", vector_manifest)
    monkeypatch.setattr(
        evaluate_retrieval,
        "HybridRetriever",
        lambda lexical_weight=0.65, semantic_weight=0.35: HybridRetriever(FakeLexicalRetriever(), FakeSemanticRetriever()),
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


def test_comparison_report_includes_hybrid_metrics() -> None:
    results = {
        "lexical": evaluate_retrieval.mode_to_dict(evaluate_retrieval.pending_mode("lexical", 0, status="EVALUATED")),
        "semantic": evaluate_retrieval.mode_to_dict(evaluate_retrieval.pending_mode("semantic", 0, status="EVALUATED")),
        "hybrid": evaluate_retrieval.mode_to_dict(evaluate_retrieval.pending_mode("hybrid", 0, status="EVALUATED")),
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
        lambda lexical_weight=0.65, semantic_weight=0.35: HybridRetriever(FakeLexicalRetriever(), FakeSemanticRetriever()),
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

