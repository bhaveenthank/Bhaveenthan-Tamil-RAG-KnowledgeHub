from knowledge.build_saanrugraph_phase3_gold_set import cohen_kappa, hard_case_tags, lexical_overlap


def test_lexical_overlap_scores_token_sets() -> None:
    assert lexical_overlap("விடை ஏறி", "விடை மீது ஏறி") > 0
    assert lexical_overlap("விடை ஏறி", "அருள் புரிந்தான்") == 0


def test_hard_case_tags_include_relation_and_penalty_signals() -> None:
    row = {
        "source_text": "வெண்மதி சூடி",
        "target_text": "பிறையை முடிமிசைச் சூடி",
        "relationship_type": "interprets_image",
        "issue_tags_after": "ambiguous_span|missing_anchor",
        "penalties_applied": "ambiguous_margin_penalty",
        "quality_flags": "short_but_valid_single_token",
    }
    tags = hard_case_tags(row)
    assert "ambiguous_commentary" in tags
    assert "no_shared_entity_or_missing_anchor" in tags
    assert "poetic_imagery" in tags
    assert "single_token_phrase" in tags


def test_cohen_kappa_pending_without_labels() -> None:
    result = cohen_kappa([("", ""), ("link", "")])
    assert result["status"] == "pending_manual_annotation"
    assert result["pair_count"] == 0


def test_cohen_kappa_computes_simple_agreement() -> None:
    result = cohen_kappa([("link", "link"), ("no_link", "no_link"), ("link", "no_link")])
    assert result["status"] == "computed"
    assert result["pair_count"] == 3
    assert 0 <= result["observed_agreement"] <= 1
