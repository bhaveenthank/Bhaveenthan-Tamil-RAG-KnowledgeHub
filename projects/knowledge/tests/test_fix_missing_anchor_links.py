import json
from pathlib import Path

from knowledge.fix_missing_anchor_links import (
    detect_anchor_hits,
    load_anchor_rules,
    load_existing_ontology,
    resolve_anchors,
    run_fix,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def row(
    *,
    link_id: str,
    paadal_text: str,
    commentary_text: str,
    source: str,
    target: str,
    confidence: str = "medium",
    relationship: str = "interprets_image",
    missing_anchor: bool = True,
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
        "score": 0.84 if confidence == "high" else 0.62,
        "source_start_char": source_start,
        "source_end_char": source_start + len(source),
        "target_start_char": target_start,
        "target_end_char": target_start + len(target),
        "rule_ids_applied": [],
        "split_parent_id": "",
        "manual_review_required": confidence != "high",
        "reviewer_note": "",
        "diagnostic_note": "fixture",
        "method": "fixture",
        "penalties_applied": ["missing_entity_anchor_penalty"] if missing_anchor else [],
        "critical_warnings": [],
        "feature_scores": {},
        "expanded_entity_anchors": [],
        "sequence_alignment_method": "global_sequence_assignment",
    }


def resolver(source: str, target: str, relationship: str = "interprets_image"):
    rules, _ = load_anchor_rules()
    return resolve_anchors(source, target, relationship, rules)


def test_uses_existing_ontology_metadata() -> None:
    ontology = load_existing_ontology()
    assert ontology["ontology_schema_version"] == "thevaram-ontology-v1"
    assert "DEITY" in ontology["entity_types"]
    assert "wears" in ontology["relations"]
    assert "enshrined_at" in ontology["relations"]


def test_ganga_in_hair_anchor_resolves_with_ontology_relation() -> None:
    resolution = resolver("சூடினார், கங்கையாளைச் சுவறிடு சடையர்", "சடைமுடியில் கங்கையைத் தரித்தவர்")
    assert resolution.missing_anchor_resolved is True
    assert "GANGA" in resolution.matched_anchors
    assert "SIVA_HAIR" in resolution.matched_anchors
    assert "wears(SIVA,GANGA)" in resolution.ontology_relations


def test_crescent_in_hair_anchor_resolves() -> None:
    resolution = resolver("திரு முடி மேல் வெண்மதி சூடி", "சடைமுடியில் பிறைச் சந்திரனை அணிந்தவர்")
    assert resolution.missing_anchor_resolved is True
    assert "CRESCENT_MOON" in resolution.matched_anchors
    assert "wears(SIVA,CRESCENT_MOON)" in resolution.ontology_relations


def test_bull_riding_context_disambiguates_bull_anchor() -> None:
    resolution = resolver("விடை ஏறி அருளும் பெருமான்", "எருது மீது ஏறிவரும் சிவபெருமான்")
    assert resolution.missing_anchor_resolved is True
    assert "BULL" in resolution.matched_anchors
    assert any("rides(SIVA,BULL)" in relation or "shared_anchor(BULL)" in relation for relation in resolution.ontology_relations)


def test_aravam_sound_is_not_serpent() -> None:
    rules, _ = load_anchor_rules()
    hits = detect_anchor_hits("பறையின் அரவம் ஒலி", rules)
    assert "SOUND" in {hit.canonical for hit in hits}
    assert "SERPENT" not in {hit.canonical for hit in hits}


def test_aravu_serpent_is_serpent_anchor() -> None:
    rules, _ = load_anchor_rules()
    hits = detect_anchor_hits("அரவு அணிந்து சடைமுடி உடையவர்", rules)
    assert "SERPENT" in {hit.canonical for hit in hits}


def test_divine_feet_worship_relation_resolves() -> None:
    resolution = resolver("திருவடி தொழுது வினை நீங்கும்", "திருவடிகளை கைதொழும் அடியாரின் வினை கெடும்", "theological_explanation")
    assert resolution.missing_anchor_resolved is True
    assert "DIVINE_FEET" in resolution.matched_anchors
    assert "WORSHIP" in resolution.matched_anchors
    assert "worshipped_by(SIVA,DEVOTEE)" in resolution.ontology_relations


def test_place_based_deity_anchor_resolves() -> None:
    resolution = resolver("ஆலவாயில் இறைவர்", "திரு ஆலவாயில் எழுந்தருளிய சிவபெருமான்", "describes_entity")
    assert resolution.missing_anchor_resolved is True
    assert "AALAVAI_THALAM" in resolution.matched_anchors
    assert "SIVA" in resolution.matched_anchors
    assert "enshrined_at(SIVA,AALAVAI)" in resolution.ontology_relations


def test_sambandar_place_context_resolves() -> None:
    resolution = resolver("காழி மா நகர் வாழி சம்பந்தன்", "சீகாழியில் தோன்றிய ஞானசம்பந்தன்", "describes_entity")
    assert resolution.missing_anchor_resolved is True
    assert "SAMBANDAR" in resolution.matched_anchors
    assert "sung_at(PATIKAM,SIRKAZHI)" in resolution.ontology_relations


def test_ravana_myth_action_resolves() -> None:
    resolution = resolver("பத்துத்தலையோன் செருக்கு கால் விரலால் நெரித்த", "இராவணன் செருக்கை அடக்கிய சிவபெருமான்")
    assert resolution.missing_anchor_resolved is True
    assert "RAVANA_SUBDUING_EVENT" in resolution.matched_anchors
    assert "agent_of(SIVA,RAVANA_SUBDUING_EVENT)" in resolution.ontology_relations


def test_hand_anchor_does_not_match_inside_ganga() -> None:
    rules, _ = load_anchor_rules()
    hits = detect_anchor_hits("கங்கை சடையில் சூடியவர்", rules)
    assert "GANGA" in {hit.canonical for hit in hits}
    assert "HAND" not in {hit.canonical for hit in hits}


def test_run_fix_resolves_missing_anchor_and_preserves_prior_high_links(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    base_root = tmp_path / "base"
    output_root = tmp_path / "out"
    paadal_text = "திரு முடி மேல் வெண்மதி சூடி சூடினார், கங்கையாளைச் சுவறிடு சடையர்"
    commentary_text = "சடைமுடியில் பிறைச் சந்திரனை அணிந்தவர்; சடைமுடியில் கங்கையைத் தரித்தவர்"
    high = row(
        link_id="high1",
        paadal_text=paadal_text,
        commentary_text=commentary_text,
        source="திரு முடி மேல் வெண்மதி சூடி",
        target="சடைமுடியில் பிறைச் சந்திரனை அணிந்தவர்",
        confidence="high",
        missing_anchor=False,
    )
    medium = row(
        link_id="med1",
        paadal_text=paadal_text,
        commentary_text=commentary_text,
        source="சூடினார், கங்கையாளைச் சுவறிடு சடையர்",
        target="சடைமுடியில் கங்கையைத் தரித்தவர்",
    )
    write_jsonl(table_root / "paadalgal.jsonl", [{"paadal_id": "p1", "paadal_text": paadal_text}])
    write_jsonl(
        table_root / "commentaries.jsonl",
        [{"commentary_id": "p1_commentary", "paadal_id": "p1", "pozhppurai": commentary_text, "kurippurai": ""}],
    )
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl", [high, medium])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl", [high, medium])
    write_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl", [])

    summary = run_fix(table_root=table_root, base_root=base_root, output_root=output_root, report_path=output_root / "report.md")

    assert summary["accepted"] is True
    assert summary["prior_high_primary_links_checked"] == 1
    assert summary["prior_high_primary_links_lost"] == 0
    assert summary["primary_confidence"]["high"] == 2
    assert summary["missing_anchor_rows_resolved"] == 1
    assert (output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_anchor_changes.csv").exists()
