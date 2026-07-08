import json
from pathlib import Path

from knowledge.build_pozhippurai_error_reviewer import (
    build_error_reviewer,
    classify_issue,
    is_numeric_only_source,
)
from knowledge.build_pozhippurai_links_v4 import should_carry_forward_v3_link
from knowledge.link_thevaram_pozhippurai import line_spans
from knowledge.link_thevaram_pozhippurai_v3 import should_carry_forward_v2_link


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_classifies_numeric_only_and_generic_low_confidence() -> None:
    assert is_numeric_only_source("11")
    assert is_numeric_only_source(" 3. ")
    assert not is_numeric_only_source("கோயில்")

    assert classify_issue({"source_text": "1", "target_text": "", "confidence": "low"}) == (
        "numeric_only_source",
        [],
    )
    assert classify_issue(
        {"source_text": "கோயில்", "target_text": "திருக்கோயில் விளங்கும்", "confidence": "low"}
    ) == ("generic_token_low_confidence", ["கோயில்", "திருக்கோயில்"])
    assert classify_issue({"source_text": "கோயில்", "target_text": "", "confidence": "high"}) == ("", [])


def test_numbering_lines_are_not_link_sources() -> None:
    spans = line_spans("முதல் வரி\n1\nஇரண்டாம் வரி\n11.")

    assert [span["text"] for span in spans] == ["முதல் வரி", "இரண்டாம் வரி"]
    assert not should_carry_forward_v2_link({"source_text": "1"})
    assert not should_carry_forward_v3_link({"source_text": "11."})
    assert should_carry_forward_v3_link({"source_text": "கோயில்"})


def test_build_error_reviewer_writes_filtered_artifacts(tmp_path: Path) -> None:
    links_path = tmp_path / "links.jsonl"
    table_root = tmp_path / "tables"
    output_dir = tmp_path / "out"
    write_jsonl(
        links_path,
        [
            {
                "link_id": "numeric",
                "paadal_id": "paadal_1",
                "commentary_id": "paadal_1_commentary",
                "thirumurai_no": 3,
                "confidence": "low",
                "score": 0.2,
                "relationship_type": "glosses_word",
                "source_start_char": 13,
                "source_end_char": 14,
                "source_text": "1",
                "target_start_char": 0,
                "target_end_char": 9,
                "target_text": "உரை பகுதி",
                "diagnostic_note": "order only",
            },
            {
                "link_id": "generic",
                "paadal_id": "paadal_2",
                "commentary_id": "paadal_2_commentary",
                "thirumurai_no": 1,
                "confidence": "medium",
                "score": 0.3,
                "relationship_type": "explains_phrase",
                "source_start_char": 0,
                "source_end_char": 6,
                "source_text": "கோயில்",
                "target_start_char": 0,
                "target_end_char": 10,
                "target_text": "கோயில் உரை",
                "diagnostic_note": "medium",
            },
            {
                "link_id": "strong",
                "paadal_id": "paadal_3",
                "commentary_id": "paadal_3_commentary",
                "thirumurai_no": 1,
                "confidence": "high",
                "source_text": "சிவன்",
                "target_text": "சிவன்",
            },
        ],
    )
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {"paadal_id": "paadal_1", "paadal_text": "பாடல் வரி\n1", "global_song_no": "1"},
            {"paadal_id": "paadal_2", "paadal_text": "கோயில் பாடல்", "global_song_no": "2"},
            {"paadal_id": "paadal_3", "paadal_text": "சிவன் பாடல்", "global_song_no": "3"},
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {"commentary_id": "paadal_1_commentary", "pozhppurai": "உரை பகுதி"},
            {"commentary_id": "paadal_2_commentary", "pozhppurai": "கோயில் உரை"},
            {"commentary_id": "paadal_3_commentary", "pozhppurai": "சிவன் உரை"},
        ],
    )

    summary = build_error_reviewer(
        links_path=links_path,
        table_root=table_root,
        output_dir=output_dir,
        sample_per_issue=5,
    )

    assert summary["rows"] == 2
    assert summary["issue_counts"] == {
        "generic_token_low_confidence": 1,
        "numeric_only_source": 1,
    }
    assert Path(summary["viewer_path"]).exists()
    assert Path(summary["sample_path"]).exists()
    assert "Likely Causes" in Path(summary["report_path"]).read_text(encoding="utf-8")
