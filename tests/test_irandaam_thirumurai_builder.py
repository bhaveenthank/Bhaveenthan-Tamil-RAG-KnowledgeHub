from scraper.irandaam_thirumurai_builder import (
    HymnLink,
    build_corpus_record,
    extract_hymn_links,
    split_hymn_title,
    validate_corpus,
)
from scraper.pilot_hymn_scraper import CommentaryParts, VerseCandidate, parse_hymn_page, split_commentary_text


LEFT_URL = "https://www.tamilvu.org/slet/l4120/l4120lft.jsp"
HYMN_URL = "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664"


def test_parse_left_frame_hymn_links() -> None:
    html = """
    <html><body><ul>
      <li><a href="l4120son.jsp?subid=1664" target="right">திருப்பூந்தராய் - வினா உரை - இந்தளம்</a></li>
      <li><a href="l4120son.jsp?subid=1665" target="right">திருவலஞ்சுழி - வினாஉரை - இந்தளம்</a></li>
      <li><a href="../other.jsp">வேறு இணைப்பு</a></li>
    </ul></body></html>
    """

    links = extract_hymn_links(LEFT_URL, html)

    assert len(links) == 2
    assert links[0].hymn_id == "1664"
    assert links[0].url == HYMN_URL
    assert links[0].hymn_location == "திருப்பூந்தராய்"
    assert links[0].hymn_note == "வினா உரை"
    assert links[0].pann == "இந்தளம்"


def test_filter_valid_hymn_urls_and_dedupe() -> None:
    html = """
    <html><body>
      <a href="l4120son.jsp?subid=1664">திருப்பூந்தராய் - இந்தளம்</a>
      <a href="l4120son.jsp?subid=1664">திருப்பூந்தராய் - இந்தளம்</a>
      <a href="l4120son.jsp">missing subid</a>
      <a href="l4120uri.jsp?song_no=1470">commentary</a>
    </body></html>
    """

    links = extract_hymn_links(LEFT_URL, html)

    assert len(links) == 1
    assert links[0].hymn_id == "1664"


def test_split_hymn_title_without_hyphen_keeps_title() -> None:
    location, note, pann = split_hymn_title("திருக்கோழம்பம் இந்தளம்")

    assert location == "திருக்கோழம்பம் இந்தளம்"
    assert note == ""
    assert pann == ""


def test_parse_hymn_page_extracts_commentary_urls_for_builder() -> None:
    html = """
    <html><body>
      <td class="subhead"><b>2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்</b></td>
      <tr>
        <td class="poem">
          <table><tr>
            <td>1470.</td>
            <td>வரி ஒன்று<br>வரி இரண்டு</td>
            <td>1</td>
          </tr></table>
        </td>
        <td><a onclick="window.open('l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664')">உரை</a></td>
      </tr>
    </body></html>
    """

    title, verses = parse_hymn_page(HYMN_URL, html)

    assert title == "2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்"
    assert len(verses) == 1
    assert verses[0].commentary_url.endswith("song_no=1470&book_id=110&head_id=60&sub_id=1664")


def test_parse_commentary_page() -> None:
    html = """
    <html><body>
      <p><b>1.</b> <font><b>பொ-ரை:</b></font> பொழிப்பு உரை.</p>
      <p><b><font>கு-ரை:</font></b> குறிப்பு உரை.</p>
    </body></html>
    """

    parts = split_commentary_text(html)

    assert parts.extraction_status == "success"
    assert parts.pozhppurai == "பொழிப்பு உரை."
    assert parts.kurippurai == "குறிப்பு உரை."


def test_build_corpus_record() -> None:
    hymn = HymnLink(
        hymn_id="1664",
        title="திருப்பூந்தராய் - வினா உரை - இந்தளம்",
        url=HYMN_URL,
        hymn_location="திருப்பூந்தராய்",
        hymn_note="வினா உரை",
        pann="இந்தளம்",
    )
    verse = VerseCandidate(
        song_no="1470",
        verse_number="1",
        verse_text="வரி ஒன்று\nவரி இரண்டு",
        commentary_url="https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664",
        book_id="110",
        head_id="60",
        sub_id="1664",
    )
    commentary = CommentaryParts("பொழிப்பு", "குறிப்பு", "success", [])

    record = build_corpus_record(hymn, hymn.title, verse, 1, commentary, "2026-06-07T00:00:00+00:00")

    assert record.source_site == "https://www.tamilvu.org"
    assert record.thirumurai_number == 2
    assert record.hymn_id == "1664"
    assert record.verse_index_in_hymn == 1
    assert record.source_parameters["song_no"] == "1470"
    assert record.text_statistics["verse_lines"] == 2
    assert record.extraction_metadata["extraction_status"] == "success"


def test_validate_duplicate_song_no() -> None:
    hymn = HymnLink("1664", "திருப்பூந்தராய்", HYMN_URL, "திருப்பூந்தராய்", "", "")
    verse = VerseCandidate(
        song_no="1470",
        verse_number="1",
        verse_text="வரி",
        commentary_url="https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664",
        book_id="110",
        head_id="60",
        sub_id="1664",
    )
    commentary = CommentaryParts("பொழிப்பு", "குறிப்பு", "success", [])
    records = [
        build_corpus_record(hymn, hymn.title, verse, 1, commentary, "2026-06-07T00:00:00+00:00"),
        build_corpus_record(hymn, hymn.title, verse, 2, commentary, "2026-06-07T00:00:00+00:00"),
    ]

    result = validate_corpus(records, hymn_links_discovered=1, hymn_summaries=[])

    assert result.ok is False
    assert result.duplicate_song_no == ["1470"]
    assert result.duplicate_source_urls == [verse.commentary_url]


def test_validate_missing_commentary_fields_warns() -> None:
    hymn = HymnLink("1664", "திருப்பூந்தராய்", HYMN_URL, "திருப்பூந்தராய்", "", "")
    verse = VerseCandidate(
        song_no="1470",
        verse_number="1",
        verse_text="வரி",
        commentary_url="",
        book_id="",
        head_id="",
        sub_id="1664",
    )
    commentary = CommentaryParts("", "", "missing_commentary_url", ["missing_commentary_url"])
    record = build_corpus_record(hymn, hymn.title, verse, 1, commentary, "2026-06-07T00:00:00+00:00")

    result = validate_corpus([record], hymn_links_discovered=1, hymn_summaries=[])

    assert result.ok is True
    assert result.missing_commentary_url_count == 1
    assert result.missing_pozhppurai_count == 1
    assert result.missing_kurippurai_count == 1
