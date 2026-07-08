import csv
import json
from pathlib import Path

from knowledge.build_pozhippurai_link_qa_pack import build_review_pack


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def link_row(index: int, confidence: str, relationship: str, thirumurai_no: int) -> dict:
    return {
        "link_id": f"link_{index}",
        "paadal_id": f"paadal_{index}",
        "commentary_id": f"paadal_{index}_commentary",
        "thirumurai_no": thirumurai_no,
        "source_line_no": 1,
        "relationship_type": relationship,
        "confidence": confidence,
        "score": 0.5,
        "link_status": "no_pozhippurai" if confidence == "none" else "linked",
        "source_text": "பாடல் வரி",
        "target_text": "" if confidence == "none" else "பொழிப்புரை பகுதி",
        "source_start_char": 0,
        "source_end_char": 9,
        "target_start_char": None if confidence == "none" else 0,
        "target_end_char": None if confidence == "none" else 16,
        "features": {"token_score": 0.1, "char_score": 0.2, "entity_score": 0.3, "order_score": 1.0},
    }


def test_build_review_pack_writes_csv_and_summary(tmp_path: Path) -> None:
    links_path = tmp_path / "links.jsonl"
    rows = [
        link_row(index, confidence, relationship, (index % 8) + 1)
        for index, (confidence, relationship) in enumerate(
            [
                ("high", "glosses_word"),
                ("medium", "interprets_image"),
                ("low", "explains_phrase"),
                ("none", "unlinked"),
                ("medium", "theological_explanation"),
            ],
            start=1,
        )
    ]
    write_jsonl(links_path, rows)

    summary = build_review_pack(
        links_path=links_path,
        output_dir=tmp_path / "pack",
        report_path=tmp_path / "report.md",
        target_count=4,
    )

    assert summary["sample_count"] == 4
    output_csv = Path(summary["output_csv"])
    assert output_csv.exists()
    csv_rows = list(csv.DictReader(output_csv.open(encoding="utf-8")))
    assert len(csv_rows) == 4
    assert "manual_decision" in csv_rows[0]
    assert csv_rows[0]["allowed_decisions"]
    assert (tmp_path / "pack" / "qa_pack_summary.json").exists()
    assert "Pozhippurai Link QA" in (tmp_path / "report.md").read_text(encoding="utf-8")
