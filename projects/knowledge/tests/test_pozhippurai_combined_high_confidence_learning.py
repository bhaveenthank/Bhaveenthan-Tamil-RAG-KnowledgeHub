import json
from pathlib import Path

from knowledge.learn_pozhippurai_combined_high_confidence_patterns import run_learning


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def row(link_id: str, confidence: str, source: str, target: str, *, manual_review: bool = False) -> dict:
    paadal_id = f"p_{link_id}"
    commentary_id = f"c_{link_id}"
    return {
        "schema_version": "thevaram-pozhppurai-paadallink-v4-combined-hardened",
        "link_id": link_id,
        "base_link_id": link_id,
        "thirumurai_no": 1,
        "pathigam_id": "h1",
        "hymn_id": "h1",
        "paadal_id": paadal_id,
        "commentary_id": commentary_id,
        "source_field": "paadal_text",
        "target_field": "pozhppurai",
        "source_text": source,
        "source_text_normalized": source,
        "target_text": target,
        "relationship_type": "interprets_image",
        "confidence": confidence,
        "score": 0.84 if confidence == "high" else 0.61,
        "source_start_char": 0,
        "source_end_char": len(source),
        "target_start_char": 0,
        "target_end_char": len(target),
        "rule_ids_applied": ["LEX_IMAGE_CRESCENT_004", "ONTO_WEAR_001"],
        "split_parent_id": "",
        "manual_review_required": manual_review,
        "reviewer_note": "",
        "diagnostic_note": "fixture",
        "method": "fixture",
        "penalties_applied": [],
        "critical_warnings": [],
        "feature_scores": {
            "semantic_lexicon_score": 0.22,
            "shared_entity_anchor_score": 0.65,
            "ontology_relation_score": 0.17,
            "relationship_cue_score": 0.75,
            "gold_pattern_similarity": 0.35,
        },
        "features": {"score_margin": 0.2},
        "expanded_entity_anchors": ["BODY_PART.DIVINE_BODY.சடை", "SACRED_OBJECT.WORN_OBJECT.பிறை"],
        "sequence_alignment_method": "global_forward",
    }


def test_combined_high_learning_promotes_matching_medium_and_preserves_high(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    combined_root = tmp_path / "combined"
    output_root = tmp_path / "out"
    high_rows = [
        row(f"gold{i}", "high", "சடை மேல் வெண்திங்கள் சூடி", "சடை மீது வெண்பிறை சூடியவர்")
        for i in range(6)
    ]
    candidate = row("candidate", "medium", "சடை மேல் வெண்திங்கள் சூடி", "சடை மீது வெண்பிறை சூடியவர்", manual_review=True)
    rows = high_rows + [candidate]
    write_jsonl(table_root / "paadalgal.jsonl", [{"paadal_id": item["paadal_id"], "paadal_text": item["source_text"]} for item in rows])
    write_jsonl(
        table_root / "commentaries.jsonl",
        [{"commentary_id": item["commentary_id"], "paadal_id": item["paadal_id"], "pozhppurai": item["target_text"], "kurippurai": ""} for item in rows],
    )
    write_jsonl(combined_root / "paadal_pozhippurai_links_v4_combined_hardened_full.jsonl", rows)
    write_jsonl(combined_root / "paadal_pozhippurai_links_v4_combined_hardened_primary_clean_links.jsonl", rows)
    write_jsonl(combined_root / "paadal_pozhippurai_links_v4_combined_hardened_secondary_no_link.jsonl", [])

    summary = run_learning(table_root=table_root, combined_root=combined_root, output_root=output_root, report_path=output_root / "report.md")

    assert summary["accepted"] is True
    assert summary["learned_high_examples_used"] == 6
    assert summary["prior_high_primary_links_lost"] == 0
    assert summary["primary_promoted_to_high"] == 1
    assert summary["primary_confidence"]["high"] == 7
    assert (output_root / "paadal_pozhippurai_links_v4_combined_learned_summary.json").exists()
