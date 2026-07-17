import json
from pathlib import Path

from knowledge.fix_pozhippurai_broad_targets import (
    candidate_subspans,
    fix_row,
    is_broad_target,
    load_hardening_pack,
    run_fix,
    select_minimal_target,
)


def base_row(source: str, target: str, relationship: str = "interprets_image", confidence: str = "high") -> dict:
    return {
        "schema_version": "thevaram-pozhppurai-paadallink-v4-hardened-learned",
        "link_id": "l1",
        "paadal_id": "p1",
        "commentary_id": "p1_commentary",
        "thirumurai_no": 1,
        "source_text": source,
        "source_text_normalized": source,
        "target_text": target,
        "source_start_char": 0,
        "source_end_char": len(source),
        "target_start_char": 0,
        "target_end_char": len(target),
        "target_field": "pozhppurai",
        "relationship_type": relationship,
        "confidence": confidence,
        "score": 0.91 if confidence == "high" else 0.62,
        "manual_review_required": False,
        "penalties_applied": ["target_too_broad_penalty"],
        "critical_warnings": [],
        "feature_scores": {"neighbor_anchor_score": 1.0},
        "expanded_entity_anchors": [],
        "rule_ids_applied": [],
        "sequence_alignment_method": "global_sequence_assignment",
        "diagnostic_note": "fixture",
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_clause_splitter_creates_meaningful_clause_and_cue_candidates() -> None:
    target = "புலித்தோலை உடுத்து, அழகிய முடிமீது பொருந்திய வெண்பிறையைச்சூடிப் பலராலும் விரும்பிப் பரவப் பெறும் கடம்பூரில் எழுந்தருளியவர்"
    candidates = candidate_subspans(target)
    texts = [candidate[2] for candidate in candidates]
    assert any("வெண்பிறையைச்சூடிப்" in text for text in texts)
    assert any(candidate[3] == "single_clause" for candidate in candidates)
    assert any(candidate[3] == "cue_phrase" for candidate in candidates)


def test_minimal_selector_chooses_crescent_target() -> None:
    pack = load_hardening_pack()
    target = "புலித்தோலை உடுத்து, அழகிய முடிமீது பொருந்திய வெண்பிறையைச்சூடிப் பலராலும் விரும்பிப் பரவப் பெறும் கடம்பூரில் எழுந்தருளியவர்"
    row = base_row("விரவும் திரு முடி தன் மேல் வெண்திங்கள் சூடி", target)
    selected = select_minimal_target(row, pack)["selected"]
    assert selected is not None
    assert "வெண்பிறையைச்சூடிப்" in selected["text"]
    assert len(selected["text"]) < len(target) * 0.75


def test_minimal_selector_chooses_ganga_target() -> None:
    pack = load_hardening_pack()
    target = "விடை மீது வந்து, கங்கையைச் சூடி அதன் பெருக்கைக் குறைத்த சடையினராய், அடியார்க்கு அருள் செய்வார்"
    row = base_row("சூடினார், கங்கையாளைச் சுவறிடு சடையர் போலும்", target)
    selected = select_minimal_target(row, pack)["selected"]
    assert selected is not None
    assert "கங்கையைச் சூடி" in selected["text"]
    assert "சடையினராய்" in selected["text"]


def test_minimal_selector_chooses_divine_feet_worship_target() -> None:
    pack = load_hardening_pack()
    target = "மலர்கள் கொண்டு, பூமாலைகள் சார்த்தப்பெற்ற திருவடிகளை உள்ளம் பொருந்தக் கைதொழுவதற்கு, வினைகள் நீங்கும்"
    row = base_row("பூப் பிணை திருந்து அடி பொருந்தக் கைதொழ", target, relationship="theological_explanation")
    selected = select_minimal_target(row, pack)["selected"]
    assert selected is not None
    assert "திருவடிகளை" in selected["text"]
    assert "கைதொழுவதற்கு" in selected["text"]


def test_does_not_shrink_full_line_source() -> None:
    pack = load_hardening_pack()
    source = "விரவும் திரு முடி தன் மேல் வெண்திங்கள் சூடி அருள்செய்யும் பெருமான்"
    target = "அழகிய முடிமீது பொருந்திய வெண்பிறையைச்சூடிப் பலராலும் விரும்பிப் பரவப் பெறும் கடம்பூரில் எழுந்தருளியவர்"
    row = base_row(source, target)
    paadal_by_id = {"p1": source}
    fixed = fix_row(row, paadal_by_id, pack)
    assert not is_broad_target(row, paadal_by_id)
    assert fixed["target_shrink_applied"] is False


def test_does_not_shrink_if_subspan_loses_core_anchor() -> None:
    pack = load_hardening_pack()
    target = "அழகிய ஊரில் விளங்கும், அடியார்கள் வாழ்வர்"
    row = base_row("வெண்திங்கள் சூடி", target)
    selected = select_minimal_target(row, pack)["selected"]
    assert selected is None


def test_run_fix_decreases_broad_target_and_preserves_high(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    base_root = tmp_path / "base"
    output_root = tmp_path / "out"
    target = "புலித்தோலை உடுத்து, அழகிய முடிமீது பொருந்திய வெண்பிறையைச்சூடிப் பலராலும் விரும்பிப் பரவப் பெறும் கடம்பூரில் எழுந்தருளியவர்"
    row = base_row("விரவும் திரு முடி தன் மேல் வெண்திங்கள் சூடி", target)
    write_jsonl(table_root / "paadalgal.jsonl", [{"paadal_id": "p1", "paadal_text": row["source_text"] + " அருள்"}])
    write_jsonl(table_root / "commentaries.jsonl", [{"commentary_id": "p1_commentary", "paadal_id": "p1", "pozhppurai": target}])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl", [row])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl", [row])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl", [])

    summary = run_fix(table_root=table_root, base_root=base_root, output_root=output_root, report_path=output_root / "report.md")

    assert summary["accepted"] is True
    assert summary["baseline"]["primary_confidence"]["high"] == 1
    assert summary["primary_confidence"]["high"] == 1
    assert summary["baseline"]["primary_broad_target_count"] == 1
    assert summary["primary_broad_target_count"] == 0
    assert summary["target_shrink_applied_count"] == 1
