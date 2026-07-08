import csv
import json
from pathlib import Path

from knowledge.review_pozhippurai_link_qa_pack import review_file


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_review_file_applies_gold_and_preserves_link_id(tmp_path: Path) -> None:
    qa_csv = tmp_path / "qa.csv"
    v2_links = tmp_path / "links.jsonl"
    output_csv = tmp_path / "reviewed.csv"
    report = tmp_path / "report.md"
    rows = [
        {
            "qa_id": "PPL_QA_001",
            "sample_reason": "test",
            "link_id": "stable_link_1",
            "paadal_id": "paadal_1",
            "commentary_id": "paadal_1_commentary",
            "thirumurai_no": "1",
            "source_line_no": "1",
            "relationship_type_v1": "glosses_word",
            "confidence_v1": "low",
            "score_v1": "0.1",
            "link_status_v1": "linked_low_confidence",
            "source_text": "புக்கிட்டு,",
            "target_text": "தவறான உரை",
            "source_offsets": "0:10",
            "target_offsets": "0:10",
            "token_score": "0",
            "char_score": "0",
            "entity_score": "0",
            "order_score": "0.5",
            "review_question": "?",
            "allowed_decisions": "ACCEPT|WRONG_TARGET",
            "manual_decision": "",
            "correct_relationship_type": "",
            "correct_target_text_or_note": "",
            "v2_rule_suggestion": "",
            "reviewer_notes": "",
        }
    ]
    write_csv(qa_csv, rows)
    write_jsonl(v2_links, [])

    summary = review_file(
        qa_csv=qa_csv,
        v2_links_path=v2_links,
        output_csv=output_csv,
        report_path=report,
        prefer_v2_target=True,
    )

    assert summary["validation"]["status"] == "VALID"
    reviewed = list(csv.DictReader(output_csv.open(encoding="utf-8")))
    assert reviewed[0]["link_id"] == "stable_link_1"
    assert reviewed[0]["manual_decision"] == "WRONG_TARGET"
    assert reviewed[0]["correct_relationship_type"] == "explains_phrase"
    assert reviewed[0]["correct_target_text_or_note"] == "தேடப் புகுந்து"
    assert reviewed[0]["updated_confidence"] == "HIGH"
    assert "Phase 3" in report.read_text(encoding="utf-8")
