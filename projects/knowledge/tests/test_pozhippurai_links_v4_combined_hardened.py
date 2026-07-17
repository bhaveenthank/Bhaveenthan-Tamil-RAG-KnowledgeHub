import json
from pathlib import Path

from knowledge.build_pozhippurai_links_v4_combined_hardened import run_combined


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def make_row(
    *,
    link_id: str,
    paadal_id: str,
    commentary_id: str,
    paadal_text: str,
    commentary_text: str,
    source: str,
    target: str,
    relationship: str = "interprets_image",
    confidence: str = "medium",
    penalties: list[str] | None = None,
    critical: list[str] | None = None,
    manual_review: bool = True,
) -> dict:
    source_start = paadal_text.index(source)
    target_start = commentary_text.index(target)
    return {
        "schema_version": "thevaram-pozhppurai-paadallink-v4-hardened-learned",
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
        "relationship_type": relationship,
        "confidence": confidence,
        "score": 0.84 if confidence == "high" else 0.62 if confidence == "medium" else 0.42,
        "source_start_char": source_start,
        "source_end_char": source_start + len(source),
        "target_start_char": target_start,
        "target_end_char": target_start + len(target),
        "rule_ids_applied": [],
        "split_parent_id": "",
        "manual_review_required": manual_review,
        "reviewer_note": "",
        "diagnostic_note": "best target is close to second best",
        "method": "fixture",
        "penalties_applied": penalties or [],
        "critical_warnings": critical or [],
        "feature_scores": {
            "semantic_lexicon_score": 0.22,
            "shared_entity_anchor_score": 0.5,
            "ontology_relation_score": 0.17,
            "relationship_cue_score": 0.5,
            "neighbor_anchor_score": 1.0,
        },
        "features": {"score_margin": 0.01, "second_best_score": 0.41},
        "expanded_entity_anchors": [],
        "sequence_alignment_method": "global_sequence_assignment",
    }


def test_combined_hardening_improves_all_three_blockers_and_preserves_high(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    base_root = tmp_path / "base"
    output_root = tmp_path / "out"

    p1 = "அருள் செய் பெருமான் வெண்திங்கள் சூடி"
    c1 = "ஆலவாயில் எழுந்தருளிய இறைவனும், சடை மீது வெண்பிறை சூடியவரும்"
    broad = make_row(
        link_id="broad1",
        paadal_id="p1",
        commentary_id="c1",
        paadal_text=p1,
        commentary_text=c1,
        source="வெண்திங்கள் சூடி",
        target=c1,
        penalties=["target_too_broad_penalty"],
    )

    p2 = "சூடினார், கங்கையாளைச் சுவறிடு சடையர்"
    c2 = "சடைமுடியில் கங்கையைத் தரித்தவர்"
    missing = make_row(
        link_id="missing1",
        paadal_id="p2",
        commentary_id="c2",
        paadal_text=p2,
        commentary_text=c2,
        source=p2,
        target=c2,
        penalties=["missing_entity_anchor_penalty"],
    )

    p3 = "செஞ்சடைக்கு ஓர் வெண்திங்கள் சூடினாரும்"
    c3 = "ஆலவாயில் எழுந்தருளிய இறைவனும், செஞ்சடையில் வெண்பிறை சூடியவரும்"
    ambiguous = make_row(
        link_id="ambiguous1",
        paadal_id="p3",
        commentary_id="c3",
        paadal_text=p3,
        commentary_text=c3,
        source=p3,
        target="ஆலவாயில் எழுந்தருளிய இறைவனும்",
        penalties=["ambiguous_margin_penalty"],
        critical=["best_second_margin_below_review_threshold"],
    )

    p4 = "திரு அடிகளே"
    c4 = "திருவடிகளை உடையவர்"
    high = make_row(
        link_id="high1",
        paadal_id="p4",
        commentary_id="c4",
        paadal_text=p4,
        commentary_text=c4,
        source=p4,
        target=c4,
        relationship="describes_entity",
        confidence="high",
        penalties=[],
        critical=[],
        manual_review=False,
    )

    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {"paadal_id": "p1", "paadal_text": p1},
            {"paadal_id": "p2", "paadal_text": p2},
            {"paadal_id": "p3", "paadal_text": p3},
            {"paadal_id": "p4", "paadal_text": p4},
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {"commentary_id": "c1", "paadal_id": "p1", "pozhppurai": c1, "kurippurai": ""},
            {"commentary_id": "c2", "paadal_id": "p2", "pozhppurai": c2, "kurippurai": ""},
            {"commentary_id": "c3", "paadal_id": "p3", "pozhppurai": c3, "kurippurai": ""},
            {"commentary_id": "c4", "paadal_id": "p4", "pozhppurai": c4, "kurippurai": ""},
        ],
    )
    rows = [broad, missing, ambiguous, high]
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl", rows)
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl", rows)
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl", [])

    summary = run_combined(table_root=table_root, base_root=base_root, output_root=output_root, report_path=output_root / "report.md")

    assert summary["accepted"] is True
    assert summary["prior_high_primary_links_lost"] == 0
    assert summary["primary_confidence"]["high"] >= 1
    assert summary["broad_target_rows_resolved"] >= 1
    assert summary["missing_anchor_rows_resolved"] >= 1
    assert summary["ambiguous_rows_resolved"] >= 1
    assert (output_root / "paadal_pozhippurai_links_v4_combined_hardened_summary.json").exists()
