from knowledge.build_pozhippurai_links_v5_auto_hardened import (
    apply_v5_row,
    phrase_family_matches,
    polysemy_resolution,
    semantic_paraphrase_score,
)
from knowledge.fix_missing_anchor_links import load_anchor_rules, resolve_anchors


def base_row(**overrides: object) -> dict:
    row = {
        "link_id": "test_link",
        "base_link_id": "test_link",
        "confidence": "medium",
        "score": 0.62,
        "relationship_type": "interprets_image",
        "source_text": "சடைமுடிமேல் நீர் ஆர் கங்கை",
        "target_text": "நீண்ட சடையில் கங்கை சூடியாய்",
        "penalties_applied": ["missing_entity_anchor_penalty"],
        "critical_warnings": [],
        "feature_scores": {
            "semantic_lexicon_score": 0.2,
            "shared_entity_anchor_score": 0.2,
            "ontology_relation_score": 0.2,
            "relationship_cue_score": 0.2,
            "gold_pattern_similarity": 0.1,
        },
        "learned_pattern_score": 0.7,
        "expanded_entity_anchors": [],
        "manual_review_required": True,
        "best_second_margin": 0.14,
        "target_reuse_allowed": True,
    }
    row.update(overrides)
    return row


def test_anchor_resolver_detects_ganga_hair_image() -> None:
    rules, _ontology = load_anchor_rules()
    result = resolve_anchors("சடைமுடிமேல் நீர் ஆர் கங்கை", "நீண்ட சடையில் கங்கை சூடியாய்", "interprets_image", rules)
    assert "GANGA" in result.matched_anchors
    assert "SIVA_HAIR" in result.matched_anchors
    assert "wears(SIVA,GANGA)" in result.ontology_relations
    assert result.polysemy_safety_score >= 0.7


def test_anchor_resolver_detects_crescent_hair_image() -> None:
    rules, _ontology = load_anchor_rules()
    result = resolve_anchors("வெண்மதி கெழுவும் சடை தன் மேல்", "வெள்ளிய பிறைமதி பொருந்திய சடை முடிமேல்", "interprets_image", rules)
    assert "CRESCENT_MOON" in result.matched_anchors
    assert "SIVA_HAIR" in result.matched_anchors
    assert "wears(SIVA,CRESCENT_MOON)" in result.ontology_relations


def test_polysemy_resolves_aravam_as_sound_not_serpent() -> None:
    note, score = polysemy_resolution(base_row(source_text="அரவம்", target_text="பறைபோல ஆரவாரம்", relationship_type="glosses_word"))
    assert "SOUND" in note
    assert score >= 0.9


def test_polysemy_resolves_serpent_with_body_context() -> None:
    note, score = polysemy_resolution(base_row(source_text="அரவு அரையில் சாத்தி", target_text="பாம்பினை இடையில் கட்டி"))
    assert "safe" in note
    assert score >= 0.9


def test_semantic_paraphrase_scores_worship_result() -> None:
    score, families = semantic_paraphrase_score(
        base_row(
            relationship_type="theological_explanation",
            source_text="அடி பொருந்தக் கைதொழ",
            target_text="திருவடிகளை உள்ளம் பொருந்தக் கைதொழுவதற்கு",
        )
    )
    assert score >= 0.4
    assert "worship_action_result" in families


def test_v5_does_not_promote_order_only_to_high() -> None:
    rules, _ontology = load_anchor_rules()
    row, _change, unsafe = apply_v5_row(
        base_row(
            source_text="அடைய நின்ற அடிகளே",
            target_text="வெண்மையான திருநீற்றைப் பூசுபவர்",
            relationship_type="interprets_image",
            confidence="medium",
            penalties_applied=["order_only_penalty"],
            learned_pattern_score=0.95,
            score=0.9,
        ),
        rules,
        prior_high_ids=set(),
    )
    assert row["confidence"] != "high"
    assert row["manual_review_required"] is True
    assert row["order_only_evidence_gate"] == "block"
    assert unsafe is None


def test_v5_promotes_safe_paraphrase_anchor_row() -> None:
    rules, _ontology = load_anchor_rules()
    row, change, unsafe = apply_v5_row(base_row(), rules, prior_high_ids=set())
    assert unsafe is None
    assert row["confidence"] == "high"
    assert "ANCHOR_RESOLVED" in row["repair_actions_applied"]
    assert row["semantic_paraphrase_score"] >= 0.4
    assert change is not None


def test_phrase_family_thalam_entity_match() -> None:
    matches = phrase_family_matches("ஆலவாயிலான்", "திரு ஆலவாய் இறைவனை", "describes_entity")
    assert [match.name for match in matches] == ["deity_thalam_entity"]
