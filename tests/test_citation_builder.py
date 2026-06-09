import json

import pytest

from rag.citation_builder import (
    build_citation_package,
    citation_metrics,
    render_citation_report,
    validate_citation,
    validate_citation_package,
)
from rag.export_citations import main


def context(
    context_id: str,
    record_id: str,
    chunk_id: str,
    rank: int,
    song_no: str,
) -> dict:
    return {
        "context_id": context_id,
        "rank": rank,
        "parent_record_id": record_id,
        "chunk_id": chunk_id,
        "chunk_type": "verse_plus_commentary",
        "matched_modes": ["lexical", "semantic"],
        "hybrid_score": 0.9,
        "deterministic_rank_key": f"1664:{song_no}",
        "citation": {
            "source_name": "TamilVU",
            "source_title": "திருப்பூந்தராய்",
            "citation_text": f"திருப்பூந்தராய், பாடல் {song_no}, TamilVU.",
            "author": "Sambandar",
            "collection": "Thevaram",
            "thirumurai": "Irandaam Thirumurai",
            "hymn_id": "1664",
            "song_no": song_no,
            "source_urls": [
                "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664",
                f"https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no={song_no}&sub_id=1664",
            ],
        },
    }


def context_package(include_duplicate: bool = False) -> dict:
    contexts = [
        context("ctx_001", "r1", "c1", 1, "1470"),
        context("ctx_002", "r2", "c2", 2, "1471"),
    ]
    if include_duplicate:
        contexts.append(context("ctx_003", "r1", "c1", 3, "1470"))
    return {
        "query": "திருப்பூந்தராய்",
        "retrieval_mode": "hybrid",
        "context_count": len(contexts),
        "contexts": contexts,
    }


def test_citation_creation_and_deterministic_ids() -> None:
    package = build_citation_package(context_package())

    assert package["citation_count"] == 2
    assert [citation["citation_id"] for citation in package["citations"]] == ["cit_001", "cit_002"]
    assert package["citations"][0]["source_url"].endswith("subid=1664")
    assert "uri.jsp" in package["citations"][0]["commentary_url"]
    assert package["validation"]["status"] == "valid"


def test_duplicate_handling() -> None:
    package = build_citation_package(context_package(include_duplicate=True))

    assert package["citation_count"] == 2
    assert citation_metrics(package)["duplicate_count"] == 0


def test_citation_validation() -> None:
    package = build_citation_package(context_package())
    malformed = dict(package["citations"][0])
    malformed["source_url"] = "not-a-url"
    malformed["song_no"] = ""

    errors = validate_citation(malformed)

    assert any("missing song_no" in error for error in errors)
    assert any("malformed source_url" in error for error in errors)


def test_multiple_citations_per_answer_segment() -> None:
    package = build_citation_package(
        context_package(),
        segment_citations={"segment_001": ["cit_001", "cit_002", "cit_001"]},
    )

    assert package["answer_segment_citations"] == [
        {"segment_id": "segment_001", "citation_ids": ["cit_001", "cit_002"]}
    ]


def test_unknown_segment_citation_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_citation_package(
            context_package(),
            segment_citations={"segment_001": ["cit_999"]},
        )


def test_citation_grouping() -> None:
    package = build_citation_package(context_package())

    assert len(package["citation_groups"]) == 1
    assert package["citation_groups"][0]["citation_ids"] == ["cit_001", "cit_002"]
    assert package["citation_groups"][0]["song_numbers"] == ["1470", "1471"]


def test_package_validation_detects_duplicate_citations() -> None:
    package = build_citation_package(context_package())
    package["citations"].append(dict(package["citations"][0]))
    package["citation_count"] = 3

    errors = validate_citation_package(package)

    assert any("duplicate citation" in error for error in errors)


def test_report_generation() -> None:
    package = build_citation_package(context_package())
    report = render_citation_report(package, input_path="sample_context.json")

    assert "Citation coverage: `100.00%`" in report
    assert "Source URL coverage: `100.00%`" in report
    assert "No duplicate citation records remain." in report


def test_export_generation(tmp_path) -> None:
    input_path = tmp_path / "sample_context.json"
    output_path = tmp_path / "sample_citations.json"
    report_path = tmp_path / "citation-report.md"
    input_path.write_text(
        json.dumps(context_package(), ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )
    exported = json.loads(output_path.read_text(encoding="utf-8"))

    assert result == 0
    assert exported["citation_count"] == 2
    assert report_path.exists()


def test_deterministic_output() -> None:
    first = build_citation_package(context_package())
    second = build_citation_package(context_package())

    assert first == second
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second,
        ensure_ascii=False,
        sort_keys=True,
    )

