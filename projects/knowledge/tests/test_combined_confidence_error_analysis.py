from knowledge.analyze_combined_learned_confidence_errors import classify_row


def base_row(**overrides: object) -> dict:
    row = {
        "confidence": "low",
        "relationship_type": "interprets_image",
        "source_text": "சடை மேல் வெண்மதி",
        "target_text": "பெருமான் உறையும் கோயில்",
        "penalties_applied": [],
        "critical_warnings": [],
        "feature_scores": {
            "semantic_lexicon_score": 0.0,
            "shared_entity_anchor_score": 0.0,
            "ontology_relation_score": 0.0,
            "relationship_cue_score": 0.0,
            "gold_pattern_similarity": 0.0,
        },
        "learned_pattern_score": "0.2",
        "learned_pattern_evidence": [],
        "manual_review_required": "True",
    }
    row.update(overrides)
    return row


def test_missing_anchor_with_no_ontology_support_is_classified() -> None:
    labels = classify_row(
        base_row(
            penalties_applied=["missing_entity_anchor_penalty"],
            missing_anchor_resolved="False",
            anchors_after=[],
            ontology_relations_matched=[],
        )
    )
    assert labels["primary_category"] == "missing_anchor"
    assert "no_ontology_relation_support" in labels["sub_reasons"]


def test_ambiguous_reuse_takes_priority_over_missing_anchor() -> None:
    labels = classify_row(
        base_row(
            penalties_applied=["ambiguous_margin_penalty", "missing_entity_anchor_penalty"],
            critical_warnings=["best_second_margin_below_review_threshold"],
            ambiguous_span_before="True",
            best_second_margin="0.01",
            target_reuse_reason="suspicious_target_reuse",
        )
    )
    assert labels["primary_category"] == "ambiguous_span"
    assert labels["subcategory"] == "suspicious_target_reuse"


def test_broad_target_detects_multiclause_ratio() -> None:
    labels = classify_row(
        base_row(
            source_text="பிறை சூடி",
            target_text="சிவபிரான் உறையும் கோயில், சடை மீது பிறை சூடி, அடியார்க்கு அருள் செய்பவர்",
            penalties_applied=["target_too_broad_penalty"],
        )
    )
    assert labels["primary_category"] == "broad_or_unsplit_target"
    assert "multi_clause_target_needs_split" in labels["sub_reasons"]


def test_high_pattern_but_blocked_tag_is_retained() -> None:
    labels = classify_row(
        base_row(
            penalties_applied=["missing_entity_anchor_penalty"],
            learned_pattern_score="0.5",
            learned_pattern_evidence=["token", "semantic"],
        )
    )
    assert "high_pattern_but_blocked" in labels["issue_tags"]
