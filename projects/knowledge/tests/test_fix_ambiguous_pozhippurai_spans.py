import json
from pathlib import Path

from knowledge.fix_ambiguous_pozhippurai_spans import (
    AssignmentChoice,
    Candidate,
    apply_ambiguity_fix,
    choose_assignments,
    load_hardening_pack,
    run_fix,
    update_row,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def make_row(
    *,
    link_id: str,
    paadal_text: str,
    commentary_text: str,
    source: str,
    target: str,
    relationship: str = "interprets_image",
    confidence: str = "medium",
    ambiguous: bool = True,
) -> dict:
    source_start = paadal_text.index(source)
    target_start = commentary_text.index(target)
    return {
        "schema_version": "thevaram-pozhppurai-paadallink-v4-hardened-learned",
        "link_id": link_id,
        "thirumurai_no": 1,
        "pathigam_id": "h1",
        "hymn_id": "h1",
        "paadal_id": "p1",
        "commentary_id": "p1_commentary",
        "source_field": "paadal_text",
        "target_field": "pozhppurai",
        "source_text": source,
        "source_text_normalized": source,
        "target_text": target,
        "relationship_type": relationship,
        "confidence": confidence,
        "score": 0.62 if confidence == "medium" else 0.42,
        "source_start_char": source_start,
        "source_end_char": source_start + len(source),
        "target_start_char": target_start,
        "target_end_char": target_start + len(target),
        "rule_ids_applied": [],
        "split_parent_id": "",
        "manual_review_required": ambiguous,
        "reviewer_note": "",
        "diagnostic_note": "best target is close to second best",
        "method": "fixture",
        "penalties_applied": ["ambiguous_margin_penalty"] if ambiguous else [],
        "critical_warnings": ["best_second_margin_below_review_threshold"] if ambiguous else [],
        "feature_scores": {},
        "features": {"score_margin": 0.01, "second_best_score": 0.41},
        "expanded_entity_anchors": [],
        "sequence_alignment_method": "global_sequence_assignment",
    }


def assignment_for_single(source: str, correct: str, bad: str, relationship: str = "interprets_image"):
    paadal_text = source
    commentary_text = f"{bad}, {correct}"
    row = make_row(
        link_id="l1",
        paadal_text=paadal_text,
        commentary_text=commentary_text,
        source=source,
        target=bad,
        relationship=relationship,
    )
    choices = choose_assignments([row], {"p1_commentary": {"commentary_id": "p1_commentary", "pozhppurai": commentary_text}}, load_hardening_pack())
    return choices["l1"]


def test_crescent_target_chosen_over_neighbouring_clause() -> None:
    choice = assignment_for_single(
        "செஞ்சடைக்கு ஓர் வெண்திங்கள் சூடினாரும், திரு",
        "செஞ்சடையில் வெண்பிறை சூடியவரும்",
        "ஆலவாயில் எழுந்தருளிய இறைவனும்",
    )
    assert choice.candidate.text == "செஞ்சடையில் வெண்பிறை சூடியவரும்"
    assert choice.margin >= 0.12


def test_moon_on_hair_target_is_selected() -> None:
    choice = assignment_for_single(
        "சேர் சடை மேல் மதியம் சூடி",
        "சடை மீது பிறை சூடி",
        "அடியார்க்கு அருள் செய்பவர்",
    )
    assert choice.candidate.text == "சடை மீது பிறை சூடி"


def test_moon_on_matted_hair_avoids_thalam_deity_clause() -> None:
    choice = assignment_for_single(
        "வெண்மதி கெழுவும் சடை தன் மேல்",
        "வெள்ளிய பிறைமதி பொருந்திய சடை முடிமேல்",
        "திருவண்ணாமலையில் விளங்கும் சிவபிரான்",
    )
    assert choice.candidate.text == "வெள்ளிய பிறைமதி பொருந்திய சடை முடிமேல்"


def test_worship_result_target_is_selected() -> None:
    choice = assignment_for_single(
        "அழகர் பாதம் தொழுது ஏத்த வல்லார்க்கு அழகு ஆகுமே",
        "அழகர் பாதங்களைத் தொழுது போற்றவல்லார்க்கு அழகு நலம் வாய்க்கும்",
        "நாகேச்சுரத்தில் விளங்கும் அழகர்",
        "theological_explanation",
    )
    assert choice.candidate.text == "அழகர் பாதங்களைத் தொழுது போற்றவல்லார்க்கு அழகு நலம் வாய்க்கும்"


def test_wrong_neighbouring_target_is_not_promoted() -> None:
    paadal_text = "அடைய நின்ற அடிகளே"
    commentary_text = "வெண்மையான திருநீற்றைப் பூசுபவர்"
    row = make_row(
        link_id="bad1",
        paadal_text=paadal_text,
        commentary_text=commentary_text,
        source=paadal_text,
        target=commentary_text,
        confidence="low",
    )
    fixed, changes = apply_ambiguity_fix([row], table_root_fixture(paadal_text, commentary_text), load_hardening_pack())
    assert fixed[0]["confidence"] != "high"
    assert fixed[0]["manual_review_required"] is True
    assert changes[0]["ambiguity_resolution_decision"] == "KEEP_REVIEW"


def test_low_margin_goes_to_review() -> None:
    paadal_text = "அருள் செய் பெருமான்"
    commentary_text = "அருள் செய்பவர்"
    row = make_row(
        link_id="low_margin",
        paadal_text=paadal_text,
        commentary_text=commentary_text,
        source=paadal_text,
        target="அருள் செய்பவர்",
        relationship="describes_entity",
        confidence="low",
    )
    candidate = Candidate(0, len(commentary_text), commentary_text, "pozhppurai", 0.30, {}, (), (), 0.0, True)
    second = Candidate(0, len(commentary_text), "அருள் புரிவார்", "pozhppurai", 0.28, {}, (), (), 0.0, False)
    choice = AssignmentChoice(
        candidate=candidate,
        global_score=0.30,
        best_score=0.30,
        second_score=0.27,
        margin=0.03,
        local_best=candidate,
        local_second=second,
        prev_anchor_score=0.0,
        next_anchor_score=0.0,
        neighbor_window_score=0.5,
        relation_family_consistency_score=0.5,
        relation_family_conflict_penalty=0.0,
        method="global_forward",
        forward_alignment_score=0.30,
        reverse_alignment_score=0.30,
    )
    fixed, _ = update_row(row, choice, 1, True, "unique_target")
    assert fixed["ambiguity_resolution_decision"] == "KEEP_REVIEW"


def test_target_reuse_limit_routes_weaker_reused_targets_to_review() -> None:
    paadal_text = "சடை மேல் பிறை சூடி கங்கை சூடி திருநீறு பூசி"
    commentary_text = "சடை மேல் பிறையும் கங்கையும் தரித்தவர்"
    rows = [
        make_row(link_id="r1", paadal_text=paadal_text, commentary_text=commentary_text, source="சடை மேல் பிறை சூடி", target=commentary_text),
        make_row(link_id="r2", paadal_text=paadal_text, commentary_text=commentary_text, source="கங்கை சூடி", target=commentary_text),
        make_row(link_id="r3", paadal_text=paadal_text, commentary_text=commentary_text, source="திருநீறு பூசி", target=commentary_text),
    ]
    fixed, _ = apply_ambiguity_fix(rows, table_root_fixture(paadal_text, commentary_text), load_hardening_pack())
    assert any(row["target_reuse_count"] == 3 for row in fixed)
    assert any(row["target_reuse_reason"] == "suspicious_target_reuse" for row in fixed)
    assert any(row["ambiguity_resolution_decision"] == "KEEP_REVIEW" for row in fixed)


def test_run_fix_preserves_high_and_reduces_ambiguous(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    base_root = tmp_path / "base"
    output_root = tmp_path / "out"
    paadal_text = "திரு அடிகளே செஞ்சடைக்கு ஓர் வெண்திங்கள் சூடினாரும்"
    commentary_text = "திருவடிகளை உடையவர், ஆலவாயில் எழுந்தருளிய இறைவனும், செஞ்சடையில் வெண்பிறை சூடியவரும்"
    ambiguous = make_row(
        link_id="amb1",
        paadal_text=paadal_text,
        commentary_text=commentary_text,
        source="செஞ்சடைக்கு ஓர் வெண்திங்கள் சூடினாரும்",
        target="ஆலவாயில் எழுந்தருளிய இறைவனும்",
        confidence="medium",
    )
    high = make_row(
        link_id="high1",
        paadal_text="திரு அடிகளே",
        commentary_text="திருவடிகளை உடையவர்",
        source="திரு அடிகளே",
        target="திருவடிகளை உடையவர்",
        relationship="describes_entity",
        confidence="high",
        ambiguous=False,
    )
    high["paadal_id"] = "p2"
    high["commentary_id"] = "p2_commentary"
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {"paadal_id": "p1", "paadal_text": paadal_text},
            {"paadal_id": "p2", "paadal_text": "திரு அடிகளே"},
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {"commentary_id": "p1_commentary", "paadal_id": "p1", "pozhppurai": commentary_text, "kurippurai": ""},
            {"commentary_id": "p2_commentary", "paadal_id": "p2", "pozhppurai": "திருவடிகளை உடையவர்", "kurippurai": ""},
        ],
    )
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl", [high, ambiguous])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl", [high, ambiguous])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl", [])

    summary = run_fix(table_root=table_root, base_root=base_root, output_root=output_root, report_path=output_root / "report.md")

    assert summary["accepted"] is True
    assert summary["primary_confidence"]["high"] >= 1
    assert summary["prior_high_primary_links_lost"] == 0
    assert summary["ambiguous_rows_resolved"] == 1
    assert (output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_ambiguity_changes.csv").exists()


def table_root_fixture(paadal_text: str, commentary_text: str) -> Path:
    root = Path("/private/tmp/tvu_ambiguous_span_test_fixture")
    write_jsonl(root / "paadalgal.jsonl", [{"paadal_id": "p1", "paadal_text": paadal_text}])
    write_jsonl(root / "commentaries.jsonl", [{"commentary_id": "p1_commentary", "paadal_id": "p1", "pozhppurai": commentary_text, "kurippurai": ""}])
    return root
