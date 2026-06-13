import json
from dataclasses import asdict

from scraper.pilot_hymn_scraper import (
    CommentaryParts,
    PilotRecord,
    VerseCandidate,
    build_record,
    extract_query_params,
    parse_hymn_page,
    split_commentary_text,
    validate_records,
)


HYMN_URL = "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664"


def test_parse_hymn_page_extracts_urai_commentary_urls() -> None:
    html = """
    <html><body>
      <td class="subhead"><b>2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்</b></td>
      <tr>
        <td></td>
        <td class="poem">
          <table><tr>
            <td class="pno">1470.</td>
            <td>வரி ஒன்று<br>வரி இரண்டு<br>வரி மூன்று<br>வரி நான்கு</td>
            <td>1</td>
          </tr></table>
        </td>
        <td><a href="javascript:void(0)" onclick="window.open('l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664','mywindow')">உரை</a></td>
      </tr>
    </body></html>
    """

    title, verses = parse_hymn_page(HYMN_URL, html)

    assert title == "2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்"
    assert len(verses) == 1
    assert verses[0].song_no == "1470"
    assert verses[0].verse_text == "வரி ஒன்று\nவரி இரண்டு\nவரி மூன்று\nவரி நான்கு"
    assert verses[0].commentary_url.endswith("song_no=1470&book_id=110&head_id=60&sub_id=1664")


def test_parse_hymn_page_prefers_stable_commentary_song_no() -> None:
    html = """
    <html><body>
      <tr>
        <td class="poem">
          <table><tr>
            <td class="pno">1990.</td>
            <td>வரி ஒன்று<br>வரி இரண்டு</td>
            <td>7</td>
          </tr></table>
        </td>
        <td><a href="javascript:void(0)" onclick="window.open('l4120uri.jsp?song_no=1890&book_id=110&head_id=60&sub_id=1702','mywindow')">உரை</a></td>
      </tr>
    </body></html>
    """

    _title, verses = parse_hymn_page("https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1702", html)

    assert verses[0].song_no == "1890"
    assert verses[0].verse_number == "7"


def test_extract_params_from_commentary_url() -> None:
    params = extract_query_params(
        "https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664"
    )

    assert params == {
        "song_no": "1470",
        "book_id": "110",
        "head_id": "60",
        "sub_id": "1664",
    }


def test_split_commentary_page_pozhppurai_and_kurippurai() -> None:
    html = """
    <html><body>
      <p><b>1. <font>பொழிப்புரை:</font></b> பொழிப்பு விளக்கம் ஒன்று.</p>
      <p><b>குறிப்புரை:</b> குறிப்பு விளக்கம் இரண்டு.</p>
    </body></html>
    """

    parts = split_commentary_text(html)

    assert parts.extraction_status == "success"
    assert parts.pozhppurai == "பொழிப்பு விளக்கம் ஒன்று."
    assert parts.kurippurai == "குறிப்பு விளக்கம் இரண்டு."


def test_split_commentary_page_accepts_abbreviated_labels() -> None:
    html = """
    <html><body>
      <p><b>8.</b> <font><b>பொ-ரை:</b></font> சுருக்கப் பொழிப்பு.</p>
      <p><b><font>கு-ரை:</font></b> சுருக்கக் குறிப்பு.</p>
    </body></html>
    """

    parts = split_commentary_text(html)

    assert parts.extraction_status == "success"
    assert parts.pozhppurai == "சுருக்கப் பொழிப்பு."
    assert parts.kurippurai == "சுருக்கக் குறிப்பு."


def test_split_commentary_page_accepts_semicolon_label_punctuation() -> None:
    html = """
    <html><body>
      <p><b>6.</b> <font><b>பொ-ரை;</b></font> அரை நிறுத்தப் பொழிப்பு.</p>
      <p><b><font>கு-ரை:</font></b> குறிப்பு உரை.</p>
    </body></html>
    """

    parts = split_commentary_text(html)

    assert parts.extraction_status == "success"
    assert parts.pozhppurai == "அரை நிறுத்தப் பொழிப்பு."
    assert parts.kurippurai == "குறிப்பு உரை."


def test_build_jsonl_record_shape() -> None:
    verse = VerseCandidate(
        song_no="1470",
        verse_number="1",
        verse_text="வரி ஒன்று",
        commentary_url="https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664",
        book_id="110",
        head_id="60",
        sub_id="1664",
    )
    commentary = CommentaryParts("பொழிப்பு", "குறிப்பு", "success", [])

    record = build_record(HYMN_URL, "திருப்பூந்தராய்", verse, commentary)
    payload = json.loads(json.dumps(asdict(record), ensure_ascii=False))

    assert payload["record_type"] == "verse_with_commentary"
    assert payload["source"] == "TamilVU"
    assert payload["song_no"] == "1470"
    assert payload["pozhppurai"] == "பொழிப்பு"
    assert payload["kurippurai"] == "குறிப்பு"


def test_validation_checks() -> None:
    records = [
        PilotRecord(
            record_type="verse_with_commentary",
            source="TamilVU",
            work="Panniru Thirumurai",
            collection="Thevaram",
            thirumurai="Irandaam Thirumurai",
            author="Sambandar",
            hymn_title="திருப்பூந்தராய்",
            sub_id="1664",
            book_id="110",
            head_id="60",
            song_no=str(1470 + index),
            verse_text="வரி ஒன்று",
            pozhppurai="பொழிப்பு",
            kurippurai="குறிப்பு",
            hymn_url=HYMN_URL,
            commentary_url=f"https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no={1470 + index}&book_id=110&head_id=60&sub_id=1664",
            language="ta",
            extraction_status="success",
        )
        for index in range(10)
    ]

    result = validate_records(records, commentary_url_count=10)

    assert result.ok is True
    assert result.errors == []


def test_validation_fails_for_missing_required_fields() -> None:
    record = PilotRecord(
        record_type="verse_with_commentary",
        source="TamilVU",
        work="Panniru Thirumurai",
        collection="Thevaram",
        thirumurai="Irandaam Thirumurai",
        author="Sambandar",
        hymn_title="திருப்பூந்தராய்",
        sub_id="1664",
        book_id="110",
        head_id="60",
        song_no="",
        verse_text="",
        pozhppurai="",
        kurippurai="",
        hymn_url=HYMN_URL,
        commentary_url="",
        language="ta",
        extraction_status="success",
    )

    result = validate_records([record], commentary_url_count=0)

    assert result.ok is False
    assert any("song_no" in error for error in result.errors)
    assert any("verse_text" in error for error in result.errors)
