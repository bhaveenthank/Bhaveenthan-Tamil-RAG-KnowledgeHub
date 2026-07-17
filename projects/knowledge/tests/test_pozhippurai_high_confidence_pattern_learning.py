from knowledge.learn_pozhippurai_high_confidence_patterns import (
    apply_learned_patterns,
    learn_patterns,
)


def row(
    *,
    link_id: str,
    confidence: str,
    source: str = "சடை ஆர் புனல்",
    target: str = "சடைமுடியில் கங்கையைத் தரித்தவனும்",
    relationship: str = "interprets_image",
    manual_review: bool = False,
    penalties: list[str] | None = None,
    critical: list[str] | None = None,
) -> dict:
    return {
        "link_id": link_id,
        "schema_version": "thevaram-pozhppurai-paadallink-v4-hardened",
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
        "score": 0.82 if confidence == "high" else 0.61 if confidence == "medium" else 0.34,
        "manual_review_required": manual_review,
        "rule_ids_applied": ["LEX_IMAGE_GANGA_005", "ONTO_HAIR_002"],
        "feature_scores": {
            "semantic_lexicon_score": 0.21,
            "shared_entity_anchor_score": 0.5,
            "ontology_relation_score": 0.17,
            "relationship_cue_score": 1.0,
            "gold_pattern_similarity": 0.2,
        },
        "expanded_entity_anchors": ["BODY_PART.DIVINE_BODY.சடை"],
        "sequence_alignment_method": "global_sequence_assignment",
        "penalties_applied": penalties or [],
        "critical_warnings": critical or [],
        "diagnostic_note": "fixture",
    }


def test_learns_high_patterns_and_promotes_matching_medium_to_high() -> None:
    patterns = learn_patterns([row(link_id=f"gold_{index}", confidence="high") for index in range(3)])
    learned = apply_learned_patterns([row(link_id="candidate", confidence="medium")], patterns)
    assert patterns.high_example_count == 3
    assert learned[0]["confidence"] == "high"
    assert learned[0]["learned_promotion_reason"] == "medium_to_high_by_learned_high_pattern"
    assert "learned_high_confidence_pattern" in learned[0]["rule_ids_applied"]


def test_learns_high_patterns_and_promotes_strong_low_to_high() -> None:
    patterns = learn_patterns([row(link_id=f"gold_{index}", confidence="high") for index in range(10)])
    learned = apply_learned_patterns([row(link_id="candidate", confidence="low", manual_review=True)], patterns)
    assert learned[0]["confidence"] == "high"
    assert learned[0]["manual_review_required"] is False


def test_blocked_order_only_or_ambiguous_rows_are_not_promoted() -> None:
    patterns = learn_patterns([row(link_id="gold", confidence="high")])
    learned = apply_learned_patterns(
        [
            row(
                link_id="candidate",
                confidence="medium",
                penalties=["order_only_penalty"],
                critical=["order_only_support"],
            )
        ],
        patterns,
    )
    assert learned[0]["confidence"] == "medium"
    assert learned[0]["learned_promotion_reason"] == ""


def test_non_matching_relationship_does_not_promote() -> None:
    patterns = learn_patterns([row(link_id="gold", confidence="high", relationship="interprets_image")])
    learned = apply_learned_patterns(
        [
            row(
                link_id="candidate",
                confidence="medium",
                relationship="theological_explanation",
                source="அருள் செய்வான்",
                target="அருள்புரிவான்",
            )
        ],
        patterns,
    )
    assert learned[0]["confidence"] == "medium"
    assert learned[0]["learned_pattern_score"] < 0.42
