import json
from pathlib import Path

from rag.build_context import main
from rag.context_builder import ContextBuilder, validate_context_package


class FakeHybridRetriever:
    def search(self, query: str, filters=None, top_k: int = 5) -> list[dict]:
        rows = [
            hybrid_result("r1", "c1", 1, ["both"], 0.95),
            hybrid_result("r1", "c1-duplicate", 2, ["lexical"], 0.90),
            hybrid_result("r2", "c2", 3, ["semantic"], 0.85),
            hybrid_result("r3", "c3", 4, ["both"], 0.80),
        ]
        return rows[:top_k]


def hybrid_result(
    record_id: str,
    chunk_id: str,
    rank: int,
    matched_modes: list[str],
    score: float,
) -> dict:
    return {
        "rank": rank,
        "record_id": record_id,
        "parent_record_id": record_id,
        "chunk_id": chunk_id,
        "chunk_type": "verse_plus_commentary",
        "matched_modes": matched_modes,
        "matched_fields": ["verse_text_normalized"],
        "hybrid_score": score,
        "score": score,
        "lexical_score": 100.0,
        "semantic_score": 0.5,
        "normalized_lexical_score": 1.0,
        "normalized_semantic_score": 0.8,
        "exact_match_boost": 0.05,
        "metadata_filter_boost": 0.0,
        "citation_text": f"Citation {record_id}",
        "source_urls": {
            "hymn_url": f"https://example.test/{record_id}",
            "commentary_url": f"https://example.test/{record_id}/urai",
        },
        "deterministic_rank_key": f"{rank:03d}",
    }


def enriched_record(record_id: str, song_no: str) -> dict:
    return {
        "record_id": record_id,
        "source": "TamilVU",
        "author": "Sambandar",
        "collection": "Thevaram",
        "thirumurai": "Irandaam Thirumurai",
        "hymn_id": "1664",
        "song_no": song_no,
        "hymn_title": "திருப்பூந்தராய்",
        "verse_text_normalized": f"பாடல் {song_no}",
        "pozhppurai_normalized": f"பொழிப்புரை {song_no}",
        "kurippurai_normalized": f"குறிப்புரை {song_no}",
        "metadata_text": f"திருப்பூந்தராய் பாடல் {song_no}",
        "hymn_url": f"https://example.test/{record_id}",
        "commentary_url": f"https://example.test/{record_id}/urai",
        "deterministic_rank_key": song_no,
        "citation": {
            "source_name": "TamilVU",
            "hymn_title": "திருப்பூந்தராய்",
            "song_no": song_no,
            "hymn_id": "1664",
            "citation_string": f"திருப்பூந்தராய், பாடல் {song_no}, TamilVU.",
            "author": "Sambandar",
            "collection": "Thevaram",
            "thirumurai": "Irandaam Thirumurai",
        },
    }


def write_enriched(path: Path) -> None:
    rows = [enriched_record("r1", "1470"), enriched_record("r2", "1471"), enriched_record("r3", "1472")]
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def make_builder(tmp_path: Path) -> ContextBuilder:
    enriched_path = tmp_path / "enriched.jsonl"
    write_enriched(enriched_path)
    return ContextBuilder(retriever=FakeHybridRetriever(), enriched_path=enriched_path)


def test_context_package_format_and_citations(tmp_path) -> None:
    package = make_builder(tmp_path).build("திருப்பூந்தராய்", top_k=2)

    assert package["query"] == "திருப்பூந்தராய்"
    assert package["retrieval_mode"] == "hybrid"
    assert package["context_count"] == 2
    assert package["contexts"][0]["context_id"] == "ctx_001"
    assert package["contexts"][0]["matched_modes"] == ["lexical", "semantic"]
    assert package["contexts"][0]["citation"]["source_title"] == "திருப்பூந்தராய்"
    assert package["contexts"][0]["citation"]["source_urls"]
    assert package["contexts"][0]["content"]["verse_text"]
    assert package["validation"]["status"] == "valid"


def test_deterministic_output(tmp_path) -> None:
    builder = make_builder(tmp_path)

    first = builder.build("அருள்", top_k=3)
    second = builder.build("அருள்", top_k=3)

    assert first == second
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second,
        ensure_ascii=False,
        sort_keys=True,
    )


def test_deduplication_and_top_k(tmp_path) -> None:
    package = make_builder(tmp_path).build("அருள்", top_k=2)

    assert [context["parent_record_id"] for context in package["contexts"]] == ["r1", "r2"]
    assert len({context["chunk_id"] for context in package["contexts"]}) == 2


def test_context_budget_is_deterministic(tmp_path) -> None:
    package = make_builder(tmp_path).build("அருள்", top_k=2, max_context_chars=12)

    assert package["context_limits"]["used_context_chars"] <= 12
    assert package["context_limits"]["truncated_contexts"] >= 1


def test_context_validation_detects_duplicates() -> None:
    package = {
        "context_count": 2,
        "contexts": [
            {
                "context_id": "ctx_001",
                "parent_record_id": "r1",
                "chunk_id": "c1",
                "citation": {"citation_text": "citation", "source_title": "title"},
            },
            {
                "context_id": "ctx_002",
                "parent_record_id": "r1",
                "chunk_id": "c2",
                "citation": {"citation_text": "citation", "source_title": "title"},
            },
        ],
    }

    errors = validate_context_package(package)

    assert any("duplicate parent_record_id" in error for error in errors)


def test_cli_output_generation(tmp_path) -> None:
    output_path = tmp_path / "context.json"

    result = main(
        ["--query", "திருப்பூந்தராய்", "--top-k", "2", "--output", str(output_path)],
        builder=make_builder(tmp_path),
    )
    package = json.loads(output_path.read_text(encoding="utf-8"))

    assert result == 0
    assert package["context_count"] == 2
    assert package["contexts"][0]["citation"]["citation_text"]


def test_context_builder_has_no_llm_dependency() -> None:
    source = Path("src/rag/context_builder.py").read_text(encoding="utf-8").lower()

    assert "openai" not in source
    assert "anthropic" not in source
    assert "generate_answer" not in source

