from scraper.irandaam_thirumurai_builder import HymnLink, build_corpus_record
from scraper.pilot_hymn_scraper import CommentaryParts, VerseCandidate
from validation.sample_hymn_validator import (
    detect_record_anomalies,
    select_sample_hymns,
    summarize_records,
    summarize_sample,
)


def make_hymn(index: int) -> HymnLink:
    hymn_id = str(1664 + index)
    return HymnLink(
        hymn_id=hymn_id,
        title=f"பதிகம் {index} - இந்தளம்",
        url=f"https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid={hymn_id}",
        hymn_location=f"பதிகம் {index}",
        hymn_note="",
        pann="இந்தளம்",
    )


def make_record(hymn: HymnLink, song_no: str = "1470", commentary_url: str | None = None):
    verse = VerseCandidate(
        song_no=song_no,
        verse_number="1",
        verse_text="வரி ஒன்று",
        commentary_url=commentary_url
        if commentary_url is not None
        else f"https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no={song_no}&book_id=110&head_id=60&sub_id={hymn.hymn_id}",
        book_id="110",
        head_id="60",
        sub_id=hymn.hymn_id,
    )
    commentary = CommentaryParts("பொழிப்பு", "குறிப்பு", "success", [])
    return build_corpus_record(hymn, hymn.title, verse, 1, commentary, "2026-06-07T00:00:00+00:00")


def test_select_sample_hymns_first_middle_last() -> None:
    hymns = [make_hymn(index) for index in range(20)]

    selected = select_sample_hymns(hymns, group_size=3)

    assert [group for group, _hymn in selected] == [
        "first",
        "first",
        "first",
        "middle",
        "middle",
        "middle",
        "last",
        "last",
        "last",
    ]
    assert [hymn.hymn_id for _group, hymn in selected] == [
        "1664",
        "1665",
        "1666",
        "1673",
        "1674",
        "1675",
        "1681",
        "1682",
        "1683",
    ]


def test_detect_record_anomalies_duplicate_and_url_pattern() -> None:
    hymn = make_hymn(0)
    records = [
        make_record(hymn, song_no="1470", commentary_url="https://www.tamilvu.org/slet/l4120/not-uri.jsp?song_no=1470"),
        make_record(hymn, song_no="1470"),
    ]

    anomalies = detect_record_anomalies(records, '<td class="poem">வரி</td>')

    assert "duplicate_song_no:1470" in anomalies
    assert any(item.startswith("unexpected_commentary_url:") for item in anomalies)
    assert "unusual_verse_count:2" in anomalies


def test_summarize_records_missing_commentary_fields() -> None:
    hymn = make_hymn(0)
    verse = VerseCandidate(
        song_no="1470",
        verse_number="1",
        verse_text="வரி",
        commentary_url="",
        book_id="",
        head_id="",
        sub_id=hymn.hymn_id,
    )
    commentary = CommentaryParts("", "", "missing_commentary_url", ["missing_commentary_url"])
    record = build_corpus_record(hymn, hymn.title, verse, 1, commentary, "2026-06-07T00:00:00+00:00")

    result = summarize_records(hymn, "first", [record], '<td class="poem">வரி</td>')

    assert result.success is False
    assert result.missing_pozhppurai == 1
    assert result.missing_kurippurai == 1
    assert "missing_commentary_links:1" in result.anomalies


def test_summarize_sample_metrics() -> None:
    results = [
        summarize_records(make_hymn(0), "first", [make_record(make_hymn(0))], '<td class="poem">வரி</td>'),
        summarize_records(make_hymn(1), "first", [], "", error="network error"),
    ]

    summary = summarize_sample(results)

    assert summary.sampled_hymns == 2
    assert summary.successful_hymns == 1
    assert summary.failed_hymns == 1
    assert summary.average_verses_per_hymn == 0.5
    assert summary.average_commentary_coverage == 1.0
