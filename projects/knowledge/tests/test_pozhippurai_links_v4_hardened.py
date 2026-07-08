import json
from pathlib import Path

from knowledge.build_pozhippurai_links_v4 import secondary_no_link_rows, write_iob_v4
from knowledge.build_pozhippurai_links_v4_hardened import (
    DEFAULT_HARDENING_PACK,
    base_features,
    final_score_and_confidence,
    harden_links,
    load_hardening_pack,
)


def linked_row(
    *,
    source: str,
    target: str,
    relationship: str = "interprets_image",
    confidence: str = "low",
    score: float = 0.22,
    note: str = "The paadal line and selected pozhppurai target share little surface vocabulary.",
    margin: float = 0.5,
) -> dict:
    return {
        "schema_version": "thevaram-pozhppurai-paadallink-v4",
        "link_id": "link_" + str(abs(hash((source, target))) % 100000),
        "thirumurai_no": 1,
        "paadal_id": "p1",
        "commentary_id": "p1_commentary",
        "source_field": "paadal_text",
        "target_field": "pozhppurai",
        "source_text": source,
        "source_text_normalized": source,
        "target_text": target,
        "relationship_type": relationship,
        "confidence": confidence,
        "score": score,
        "source_start_char": 0,
        "source_end_char": len(source),
        "target_start_char": 0,
        "target_end_char": len(target),
        "rule_ids_applied": [],
        "manual_review_required": confidence == "low",
        "diagnostic_note": note,
        "method": "fixture",
        "features": {"score_margin": margin},
    }


def test_hardening_pack_loads_all_spec_files() -> None:
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    assert len(pack.semantic_lexicon) >= 10
    assert len(pack.morphology_rules) >= 5
    assert len(pack.ontology_cues) >= 5
    assert len(pack.entity_expansions) >= 20
    assert pack.alignment_config["problem"] == "low_order_only_support"
    assert pack.ambiguous_config["problem"] == "low_ambiguous_multiple_targets"
    assert pack.scoring_spec["version"] == "v4_hardening_feature_spec"
    assert len(pack.uploaded_review_samples) == 150


def test_hardening_pack_relationship_labels_are_valid() -> None:
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    allowed = {
        "describes_entity",
        "explains_line",
        "explains_phrase",
        "glosses_word",
        "interprets_image",
        "theological_explanation",
    }
    assert {entry.relationship_bias for entry in pack.semantic_lexicon} <= allowed
    assert {cue.relationship_bias for cue in pack.ontology_cues} <= allowed


def test_low_surface_vocab_gap_improves_with_semantic_and_ontology_cues() -> None:
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    row = linked_row(source="சடை ஆர் புனல்", target="சடைமுடியில் கங்கையைத் தரித்தவனும்")
    features, rule_ids, anchors = base_features(row, row["source_text"], row["target_text"], "pozhppurai", pack)
    score, confidence, penalties, critical = final_score_and_confidence(row, features, row["source_text"], row["target_text"], pack)
    assert features["semantic_lexicon_score"] > 0
    assert features["ontology_relation_score"] > 0
    assert rule_ids
    assert score > row["score"]
    assert confidence in {"medium", "high"}


def test_order_only_support_cannot_become_high_without_relation_evidence() -> None:
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    row = linked_row(
        source="அடி ஒன்று",
        target="சம்பந்தமில்லா விளக்கம்",
        relationship="explains_phrase",
        score=0.7,
        note="The selected target is mainly supported by poem/commentary order, with little lexical or entity evidence.",
    )
    features, _rule_ids, _anchors = base_features(row, row["source_text"], row["target_text"], "pozhppurai", pack)
    features["sequence_consistency_score"] = 1.0
    score, confidence, penalties, critical = final_score_and_confidence(row, features, row["source_text"], row["target_text"], pack)
    assert confidence != "high"
    assert "order_only_penalty" in penalties
    assert "order_only_support" in critical


def test_missing_entity_anchor_recovers_from_expanded_hierarchy() -> None:
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    row = linked_row(
        source="நீலமாமிடற்று ஆலவாயிலான்",
        target="நீலநிறம் பொருந்திய கண்டத்தினை உடைய திரு ஆலவாய் இறைவனை",
        relationship="describes_entity",
        note="No accepted Entity v2 anchor overlaps both source and target spans.",
    )
    features, _rule_ids, anchors = base_features(row, row["source_text"], row["target_text"], "pozhppurai", pack)
    assert features["shared_entity_anchor_score"] > 0
    assert anchors


def test_ambiguous_multiple_targets_triggers_margin_review_logic() -> None:
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    row = linked_row(
        source="பிறை முடிமேல்",
        target="வெண்பிறையைச் சூடி",
        margin=0.01,
        note="The best target is close to the second-best target, so several pozhppurai spans may be plausible.",
    )
    features, _rule_ids, _anchors = base_features(row, row["source_text"], row["target_text"], "pozhppurai", pack)
    score, confidence, penalties, critical = final_score_and_confidence(row, features, row["source_text"], row["target_text"], pack)
    assert "ambiguous_margin_penalty" in penalties
    assert "best_second_margin_below_review_threshold" in critical
    assert confidence in {"low", "medium"}


def test_empty_pozhippurai_secondary_is_excluded_from_main_linked_corpus(tmp_path: Path) -> None:
    no_link = {
        "link_id": "no1",
        "paadal_id": "p1",
        "commentary_id": "p1_commentary",
        "source_text": "பாடல்",
        "target_text": "",
        "relationship_type": "unlinked",
        "confidence": "no_link",
        "source_start_char": 0,
        "source_end_char": 5,
        "target_start_char": None,
        "target_end_char": None,
    }
    secondary = secondary_no_link_rows([no_link], [{"commentary_id": "p1_commentary", "paadal_id": "p1", "pozhppurai": ""}])
    assert secondary[0]["secondary_table_reason"] == "empty_pozhippurai"


def test_harden_links_adds_required_feature_fields_and_sequence_scores(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    table_root.mkdir()
    (table_root / "commentaries.jsonl").write_text(
        json.dumps({"commentary_id": "p1_commentary", "paadal_id": "p1", "pozhppurai": "வெண்பிறையைச் சூடி, சடைமுடியில் கங்கையைத் தரித்தவனும்"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    pack = load_hardening_pack(DEFAULT_HARDENING_PACK)
    links = [
        linked_row(source="பிறை முடிமேல்", target="வெண்பிறையைச் சூடி"),
        linked_row(source="சடை ஆர் புனல்", target="சடைமுடியில் கங்கையைத் தரித்தவனும்"),
    ]
    hardened, counts = harden_links(links, table_root=table_root, pack=pack)
    assert counts["semantic_lexicon_improved_rows"] >= 2
    assert all("feature_scores" in row for row in hardened)
    assert all("penalties_applied" in row for row in hardened)
    assert all(row["sequence_alignment_method"] in {"global_sequence_assignment", "reverse_order_alignment"} for row in hardened)


def test_iob_hardened_positive_links_have_source_and_target_sides(tmp_path: Path) -> None:
    row = linked_row(source="பிறை முடிமேல்", target="வெண்பிறையைச் சூடி", confidence="high", score=0.9)
    row["manual_review_required"] = False
    output = tmp_path / "links.iob.conll"
    write_iob_v4(output, [row])
    sides_by_link: dict[str, set[str]] = {}
    for line in output.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        _token, _label, link_id, side, _relationship, _confidence = line.split("\t")
        sides_by_link.setdefault(link_id, set()).add(side)
    assert sides_by_link
    assert all({"paadal", "pozhppurai"} <= sides for sides in sides_by_link.values())
