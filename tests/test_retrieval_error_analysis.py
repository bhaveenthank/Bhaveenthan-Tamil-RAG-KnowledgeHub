import json

from evaluation.analyze_retrieval_failures import (
    analyze,
    classify_failure,
    render_report,
    write_outputs,
)


def benchmark_fixture() -> dict:
    semantic_failure = {
        "query_id": "keyword_place",
        "query_text": "records containing திருப்பூந்தராய்",
        "query_type": "keyword",
        "passed": False,
        "reciprocal_rank": 0.0,
        "missing_expected_record_ids": ["r1"],
        "missing_expected_chunk_ids": ["c1_verse_plus_commentary"],
        "results": [
            {
                "rank": 1,
                "record_id": "r2",
                "chunk_id": "c2",
                "similarity_score": 0.40,
                "citation_text": "TamilVU r2",
            }
        ],
    }
    semantic_success = {
        "query_id": "concept",
        "query_text": "அருள்",
        "query_type": "keyword",
        "passed": True,
        "reciprocal_rank": 1.0,
        "missing_expected_record_ids": [],
        "missing_expected_chunk_ids": [],
        "results": [
            {
                "rank": 1,
                "record_id": "r3",
                "chunk_id": "c3",
                "similarity_score": 0.60,
                "citation_text": "TamilVU r3",
            }
        ],
    }
    hybrid_recovery = {
        "query_id": "keyword_place",
        "query_text": "records containing திருப்பூந்தராய்",
        "query_type": "keyword",
        "passed": True,
        "results": [
            {
                "rank": 1,
                "record_id": "r1",
                "chunk_id": "c1_verse_plus_commentary",
                "hybrid_score": 0.9,
                "matched_modes": ["lexical"],
                "matched_fields": ["metadata_text"],
                "normalized_lexical_score": 1.0,
                "normalized_semantic_score": 0.0,
                "exact_match_boost": 0.05,
                "metadata_filter_boost": 0.0,
            }
        ],
    }
    return {
        "semantic": {"query_results": [semantic_failure, semantic_success]},
        "hybrid": {"query_results": [hybrid_recovery]},
    }


def golden_fixture() -> list[dict]:
    return [
        {
            "query_id": "keyword_place",
            "query_text": "records containing திருப்பூந்தராய்",
            "query_type": "keyword",
            "required_filters": {},
            "expected_record_ids": ["r1"],
            "expected_chunk_ids": ["c1_verse_plus_commentary"],
        },
        {
            "query_id": "concept",
            "query_text": "அருள்",
            "query_type": "keyword",
            "required_filters": {},
            "expected_record_ids": ["r3"],
            "expected_chunk_ids": ["c3"],
        },
    ]


def lexical_index_fixture() -> dict:
    return {"term_to_record_ids": {"திருப்பூந்தராய்": ["r1"], "அருள்": ["r3", "r4"]}}


def test_failure_detection_and_hybrid_recovery() -> None:
    result = analyze(benchmark_fixture(), golden_fixture(), lexical_index_fixture())

    assert result["summary"]["semantic_failures"] == 1
    assert result["summary"]["semantic_successes"] == 1
    assert result["summary"]["hybrid_recoveries"] == 1
    assert result["failures"][0]["hybrid_recovery"]["hybrid_rank"] == 1


def test_category_assignment() -> None:
    category, confidence, explanation, evidence = classify_failure(
        {
            "query_text": "records missing pozhppurai",
            "query_type": "commentary",
            "required_filters": {},
            "expected_chunk_ids": ["r1_verse_plus_commentary"],
        },
        lexical_index_fixture(),
    )

    assert category == "metadata mismatch"
    assert confidence == 0.98
    assert explanation
    assert "lexical_document_frequency" in evidence


def test_rare_term_category_assignment() -> None:
    category, confidence, _explanation, _evidence = classify_failure(
        {
            "query_text": "records containing திருப்பூந்தராய்",
            "query_type": "keyword",
            "required_filters": {},
            "expected_chunk_ids": ["c1_verse_plus_commentary"],
        },
        lexical_index_fixture(),
    )

    assert category == "rare term mismatch"
    assert confidence >= 0.8


def test_report_generation() -> None:
    result = analyze(benchmark_fixture(), golden_fixture(), lexical_index_fixture())
    report = render_report(result)

    assert "Failure Categories" in report
    assert "Hybrid Diagnostics" in report
    assert "rare term mismatch" in report


def test_deterministic_output(tmp_path) -> None:
    first = analyze(benchmark_fixture(), golden_fixture(), lexical_index_fixture(), benchmark_sha256="abc")
    second = analyze(benchmark_fixture(), golden_fixture(), lexical_index_fixture(), benchmark_sha256="abc")
    first_json = tmp_path / "first.json"
    first_report = tmp_path / "first.md"
    second_json = tmp_path / "second.json"
    second_report = tmp_path / "second.md"

    write_outputs(first, first_json, first_report)
    write_outputs(second, second_json, second_report)

    assert first == second
    assert first_json.read_bytes() == second_json.read_bytes()
    assert first_report.read_bytes() == second_report.read_bytes()
