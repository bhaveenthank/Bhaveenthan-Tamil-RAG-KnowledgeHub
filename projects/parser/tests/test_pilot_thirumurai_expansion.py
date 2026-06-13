import json

import pytest

from corpus.normalize_corpus import build_manifest, normalize_record
from corpus.pilot_ingest_thirumurai import (
    PILOT_CONFIGS,
    extract_hymn_links,
    ingest,
    parse_pilot_hymn,
    split_pilot_commentary,
)
from corpus.validate_corpus import validate_records


NAV_HTML = """
<html><body>
<a href="l4130son.jsp?subid=1912">திருஅதிகைவீரட்டானம் - கொல்லி</a>
<a href="l4130son.jsp?subid=1913">திருஅதிகைவீரட்டானம் - காந்தாரம்</a>
</body></html>
"""
HYMN_HTML = """
<html><body><td class="subhead">4.1 திருஅதிகைவீரட்டானம்</td>
<tr><td class="poem"><table><tr><td class="pno">1</td><td class="poem">வரி ஒன்று<br>வரி இரண்டு</td></tr></table></td>
<td><a onclick="window.open('l4140uri.jsp?song_no=1&book_id=112&head_id=62&sub_id=1912')">உரை</a></td></tr>
</body></html>
"""
COMMENTARY_HTML = """
<html><body><p>1. பொ-ரை: பொழிப்பு உரை.</p>
<p>பொருள்: பொருள் விளக்கம்.</p><p>விளக்கம்: விரிவான குறிப்பு.</p></body></html>
"""


def raw_record() -> dict:
    return {
        "author": "Tirunavukkarasar (Appar)",
        "nayanmar": "Tirunavukkarasar",
        "hymn_id": "1912",
        "song_no": "1",
        "verse_index_in_hymn": 1,
        "hymn_title": "4.1 திருஅதிகைவீரட்டானம்",
        "hymn_location": "திருஅதிகைவீரட்டானம்",
        "hymn_note": "",
        "pann": "கொல்லி",
        "verse_text": "தமிழ் பாடல் வரி",
        "pozhppurai": "பொழிப்பு",
        "kurippurai": "குறிப்பு",
        "hymn_url": "https://www.tamilvu.org/slet/l4140/l4130son.jsp?subid=1912",
        "commentary_url": "https://www.tamilvu.org/slet/l4140/l4140uri.jsp?song_no=1&sub_id=1912",
        "source": "TamilVU",
        "source_site": "https://www.tamilvu.org",
        "work": "Panniru Thirumurai",
        "collection": "Thevaram",
        "commentary_available": True,
        "extraction_metadata": {"extraction_status": "success"},
    }


def test_target_selection_is_restricted() -> None:
    assert PILOT_CONFIGS[4]["pilot_hymn_limit"] == 5
    with pytest.raises(ValueError):
        ingest(5, 0, 1, True, None)


def test_navigation_and_hymn_parsing() -> None:
    links = extract_hymn_links(PILOT_CONFIGS[4], NAV_HTML)
    title, verses = parse_pilot_hymn(links[0].url, HYMN_HTML)

    assert len(links) == 2
    assert title == "4.1 திருஅதிகைவீரட்டானம்"
    assert verses[0]["song_no"] == "1"
    assert "l4140uri.jsp" in verses[0]["commentary_url"]


def test_commentary_labels_are_mapped() -> None:
    pozh, kuri, status, warnings = split_pilot_commentary(COMMENTARY_HTML)

    assert pozh == "பொழிப்பு உரை."
    assert "பொருள் விளக்கம்" in kuri
    assert "விரிவான குறிப்பு" in kuri
    assert status == "success"
    assert warnings == []


def test_pilot_normalized_output_follows_unified_schema() -> None:
    normalized = normalize_record(raw_record(), "thirumurai_04")
    result = validate_records([normalized])

    assert result["status"] == "VALID"
    assert normalized["record_id"] == "thevaram_04_1912_1"
    assert normalized["corpus_id"] == "thirumurai_04"
    assert normalized["author"] == "Tirunavukkarasar"


def test_validation_catches_missing_fields() -> None:
    normalized = normalize_record(raw_record(), "thirumurai_04")
    normalized["verse_text"] = ""

    result = validate_records([normalized])

    assert result["status"] == "INVALID"
    assert result["missing_fields"]["verse_text"] == 1


def test_manifest_includes_both_corpora() -> None:
    pilot = normalize_record(raw_record(), "thirumurai_04")
    registry = {
        "corpora": [
            {"corpus_id": f"thirumurai_{number:02d}", "status": "available" if number in {2, 4} else "planned"}
            for number in range(1, 13)
        ]
    }
    manifest = build_manifest(
        registry,
        [pilot],
        existing_manifest={"per_corpus_record_counts": {"thirumurai_02": 1331}},
    )

    assert manifest["normalized_corpora"] == ["thirumurai_02", "thirumurai_04"]
    assert manifest["total_normalized_records"] == 1332


def test_ingestion_paths_do_not_overwrite_thirumurai_02(tmp_path, monkeypatch) -> None:
    existing = tmp_path / "data/processed/normalized/thirumurai_02_normalized.jsonl"
    existing.parent.mkdir(parents=True)
    existing.write_text("frozen\n", encoding="utf-8")

    def fake_snapshot(url, directory, timeout, resume):
        if "l4140lft" in url:
            return NAV_HTML
        if "son.jsp" in url:
            return HYMN_HTML
        return COMMENTARY_HTML

    monkeypatch.setattr("corpus.pilot_ingest_thirumurai.snapshot", fake_snapshot)
    records, summary = ingest(4, 0, 1, True, tmp_path)

    assert records
    assert existing.read_text(encoding="utf-8") == "frozen\n"
    assert "data/processed/pilot/thirumurai_04.jsonl" in summary["output"]
