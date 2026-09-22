from pathlib import Path

from knowledge.build_saanrugraph_phase2_clean_data import (
    build_candidate_pool,
    classify_link_candidate,
    classify_text_quality,
    is_numeric_only,
    substring_matches,
)


def test_numeric_only_detects_digits_and_tamil_number_words() -> None:
    assert is_numeric_only("12")
    assert is_numeric_only("௧")
    assert is_numeric_only("ஒன்று")
    assert not is_numeric_only("ஓர் தூ வெண்மதி")


def test_text_quality_rejects_noise_but_keeps_real_single_token() -> None:
    assert classify_text_quality("-").status == "reject"
    assert classify_text_quality("123").status == "reject"
    assert classify_text_quality("உடைய").status == "reject"
    quality = classify_text_quality("தீ")
    assert quality.status == "keep"
    assert "short_but_valid_single_token" in quality.flags


def test_substring_matches_exact_offsets() -> None:
    parent = "தோடு உடைய செவியன்"
    assert substring_matches(parent, "உடைய", 5, 9)
    assert not substring_matches(parent, "செவி", 0, 4)


def test_candidate_pool_excludes_non_pozhippurai_target() -> None:
    row = {
        "link_id": "x",
        "paadal_id": "thirumurai_01_paadal_1",
        "commentary_id": "thirumurai_01_paadal_1_commentary",
        "thirumurai_no": "1",
        "source_field": "paadal_text",
        "target_field": "kurippurai",
        "source_text": "தோடு உடைய செவியன்",
        "target_text": "தோடுடையசெவியன் என்பது",
        "source_start_char": "0",
        "source_end_char": "17",
        "target_start_char": "0",
        "target_end_char": "22",
        "full_paadal_text": "தோடு உடைய செவியன்",
        "full_pozhippurai": "தோடுடையசெவியன் என்பது",
    }
    status, reasons = classify_link_candidate(row)
    assert status == "reject"
    assert "target_field_not_pozhippurai" in reasons


def test_candidate_pool_keeps_valid_pozhippurai_link() -> None:
    row = {
        "link_id": "x",
        "paadal_id": "thirumurai_01_paadal_1",
        "commentary_id": "thirumurai_01_paadal_1_commentary",
        "thirumurai_no": "1",
        "pathigam_id": "thirumurai_01_thogupu_1529",
        "hymn_id": "thirumurai_01_thogupu_1529",
        "confidence": "high",
        "score": "0.99",
        "manual_review_required": "False",
        "relationship_type": "explains_phrase",
        "source_field": "paadal_text",
        "target_field": "pozhppurai",
        "source_text": "தோடு உடைய செவியன்",
        "target_text": "தோடணிந்த திருச்செவியை உடைய",
        "source_start_char": "0",
        "source_end_char": "17",
        "target_start_char": "0",
        "target_end_char": "26",
        "full_paadal_text": "தோடு உடைய செவியன்",
        "full_pozhippurai": "தோடணிந்த திருச்செவியை உடைய",
    }
    kept, excluded, summary = build_candidate_pool([row])
    assert len(kept) == 1
    assert not excluded
    assert summary["clean_candidate_rows"] == 1
