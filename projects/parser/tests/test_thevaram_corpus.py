from pathlib import Path

from scraper.thevaram_corpus import (
    THIRUMURAI_CONFIGS,
    commentary_spans,
    extract_thogupu_links,
    fetch_attempts,
    http_variant,
    line_spans,
    parse_corpus_filter,
    parse_paadal_page,
    scrape_configs,
    slet_referer,
    split_title,
    tokenize_tamil_text,
    Commentary,
)


def test_split_title_preserves_place_note_and_pann() -> None:
    assert split_title("திருப்பிரமபுரம் - மொழிமாற்று - வியாழக்குறிஞ்சி") == (
        "திருப்பிரமபுரம்",
        "மொழிமாற்று",
        "வியாழக்குறிஞ்சி",
    )
    assert split_title("சிவபுராணம்") == ("சிவபுராணம்", "", "")


def test_extract_first_thirumurai_thogupu_links() -> None:
    html = """
    <html><body>
      <a href="l4110son.jsp?subid=1529">திருப்பிரமபுரம் - நட்டபாடை</a>
      <a href="l4110son.jsp?subid=1529">திருப்பிரமபுரம் - நட்டபாடை</a>
      <a href="l4110uri.jsp?song_no=1">உரை</a>
    </body></html>
    """

    links = extract_thogupu_links(
        THIRUMURAI_CONFIGS[1],
        "https://www.tamilvu.org/slet/l4110/l4110lft.jsp",
        html,
    )

    assert len(links) == 1
    assert links[0].thogupu_id == "thirumurai_01_thogupu_1529"
    assert links[0].paadapatta_thalam == "திருப்பிரமபுரம்"
    assert links[0].pann == "நட்டபாடை"


def test_parse_paadal_page_extracts_verse_and_commentary_link() -> None:
    thogupu = extract_thogupu_links(
        THIRUMURAI_CONFIGS[1],
        "https://www.tamilvu.org/slet/l4110/l4110lft.jsp",
        '<a href="l4110son.jsp?subid=1529">திருப்பிரமபுரம் - நட்டபாடை</a>',
    )[0]
    html = """
    <html><body>
      <tr>
        <td class="poem">
          <table><tr>
            <td>1.</td>
            <td>தோடுடைய செவியன்<br>விடையேறி</td>
            <td>1</td>
          </tr></table>
        </td>
        <td><a onclick="window.open('l4110uri.jsp?song_no=1&book_id=109&head_id=59&sub_id=1529')">உரை</a></td>
      </tr>
    </body></html>
    """

    paadalgal = parse_paadal_page(THIRUMURAI_CONFIGS[1], thogupu, html)

    assert len(paadalgal) == 1
    assert paadalgal[0].paadal_id == "thirumurai_01_paadal_1"
    assert paadalgal[0].tokenized_paadal == ["தோடுடைய", "செவியன்", "விடையேறி"]
    assert paadalgal[0].commentary_url.endswith("sub_id=1529")


def test_parse_paadal_page_supports_direct_poem_row_layout() -> None:
    thogupu = extract_thogupu_links(
        THIRUMURAI_CONFIGS[1],
        "https://www.tamilvu.org/slet/l4110/l4110lft.jsp",
        '<a href="l4110son.jsp?subid=1529">திருப்பிரமபுரம் - நட்டபாடை</a>',
    )[0]
    html = """
    <html><body><table>
      <tr>
        <td class="pno">1.</td>
        <td class="poem">தோடு உடைய செவியன்<br>காடு உடைய சுடலை</td>
        <td class="pno"><a onclick="window.open('l4110uri.jsp?song_no=1&book_id=109&head_id=59&sub_id=1529')">உரை</a></td>
      </tr>
    </table></body></html>
    """

    paadalgal = parse_paadal_page(THIRUMURAI_CONFIGS[1], thogupu, html)

    assert len(paadalgal) == 1
    assert paadalgal[0].global_song_no == "1"
    assert paadalgal[0].paadal_text == "தோடு உடைய செவியன்\nகாடு உடைய சுடலை"


def test_parse_paadal_page_supports_separate_commentary_table_layout() -> None:
    thogupu = extract_thogupu_links(
        THIRUMURAI_CONFIGS[5],
        "https://www.tamilvu.org/slet/l4150/l4150lft.jsp",
        '<a href="l4150son.jsp?subid=2079">திருவாஞ்சியம் - திருக்குறுந்தொகை</a>',
    )[0]
    html = """
    <html><body>
      <tr><td class="poem">
        <table>
          <tr><td class="pno">பாடல் எண் :1743</td></tr>
          <tr><td><table class="tamil"><tr><td>
            <p><strong>படையும் பூதமும்<br>உடையும் தாங்கிய</strong></p>
          </td></tr></table></td></tr>
          <tr><td class="pn">1</td></tr>
        </table>
      </td></tr>
      <table><tr><td class="pno">
        <a onclick="window.open('l4150uri.jsp?song_no=1743&book_id=113&head_id=63&sub_id=2079')">உரை</a>
      </td></tr></table>
    </body></html>
    """

    paadalgal = parse_paadal_page(THIRUMURAI_CONFIGS[5], thogupu, html)

    assert len(paadalgal) == 1
    assert paadalgal[0].global_song_no == "1743"
    assert paadalgal[0].local_song_no == "1743"
    assert paadalgal[0].paadal_text == "படையும் பூதமும்\nஉடையும் தாங்கிய"


def test_parse_paadal_page_supports_nested_poem_cell_layout() -> None:
    thogupu = extract_thogupu_links(
        THIRUMURAI_CONFIGS[8],
        "https://www.tamilvu.org/slet/l4180/l4180lft.jsp",
        '<a href="l4180son.jsp?subid=2314">மெய்யுணர்தல்</a>',
    )[0]
    html = """
    <html><body><table>
      <tr>
        <td class="pno"></td>
        <td class="poem"><table><tr><td class="poem">மெய் தான் அரும்பி<br>கை தான் தலை வைத்து</td></tr></table></td>
        <td class="pno">
          <a onclick="window.open('l4180uri.jsp?song_no=129&book_id=116&head_id=66&sub_id=2314')">உரை</a>
        </td>
      </tr>
    </table></body></html>
    """

    paadalgal = parse_paadal_page(THIRUMURAI_CONFIGS[8], thogupu, html)

    assert len(paadalgal) == 1
    assert paadalgal[0].global_song_no == "129"
    assert paadalgal[0].paadal_text == "மெய் தான் அரும்பி\nகை தான் தலை வைத்து"


def test_parse_paadal_page_suffixes_duplicate_source_song_numbers() -> None:
    thogupu = extract_thogupu_links(
        THIRUMURAI_CONFIGS[7],
        "https://www.tamilvu.org/slet/l4170/l4170lft.jsp",
        '<a href="l4170son.jsp?subid=2211">கோயில்</a>',
    )[0]
    html = """
    <html><body><table>
      <tr>
        <td class="pno"></td>
        <td class="poem"><table><tr><td class="pno">7</td><td class="poem">சிங்கத்து உரி<br>கங்கைச் சடையீர்</td></tr></table></td>
        <td class="pno">
          <a onclick="window.open('l4170uri.jsp?song_no=447&book_id=115&head_id=65&sub_id=2211')">உரை</a>
        </td>
      </tr>
      <tr>
        <td class="pno"></td>
        <td class="poem"><table><tr><td class="pno">8</td><td class="poem">பிணி வண்ணத்த<br>மணி வண்ணத்தின்</td></tr></table></td>
        <td class="pno">
          <a onclick="window.open('l4170uri.jsp?song_no=447&book_id=115&head_id=65&sub_id=2211')">உரை</a>
        </td>
      </tr>
    </table></body></html>
    """

    paadalgal = parse_paadal_page(THIRUMURAI_CONFIGS[7], thogupu, html)

    assert [paadal.paadal_id for paadal in paadalgal] == [
        "thirumurai_07_paadal_447",
        "thirumurai_07_paadal_447_2211_2",
    ]
    assert [paadal.global_song_no for paadal in paadalgal] == ["447", "447_2211_2"]
    assert [paadal.source_song_no for paadal in paadalgal] == ["447", "447"]
    assert [paadal.local_song_no for paadal in paadalgal] == ["7", "8"]


def test_text_spans_record_offsets() -> None:
    spans = line_spans("p1", "paadal_text", "paadal_line", "வரி ஒன்று\nவரி இரண்டு")

    assert [span.start_char for span in spans] == [0, 10]
    assert [span.end_char for span in spans] == [9, 20]


def test_commentary_spans_split_kurippurai_and_pozhppurai() -> None:
    commentary = Commentary(
        "c1",
        "p1",
        "குறிப்பு ஒன்று\nகுறிப்பு இரண்டு",
        "பொழிப்பு ஒன்று",
        "success",
        [],
    )

    spans = commentary_spans(commentary)

    assert {span.span_type for span in spans} == {
        "commentary_kurippurai",
        "commentary_pozhppurai",
    }


def test_dry_run_writes_table_outputs_from_fixture_snapshot(tmp_path) -> None:
    config = THIRUMURAI_CONFIGS[1]
    nav_dir = tmp_path / "data/raw/corpus/thevaram/thirumurai_01/navigation"
    nav_dir.mkdir(parents=True)
    from tvu_common.snapshot import save_snapshot

    save_snapshot(
        config.left_frame_url,
        '<a href="l4110son.jsp?subid=1529">திருப்பிரமபுரம் - நட்டபாடை</a>',
        nav_dir,
    )

    summary = scrape_configs(
        [config],
        base_dir=tmp_path,
        delay=0,
        timeout=1,
        resume=True,
        dry_run=True,
        fetch_missing=True,
        limit_thogupugal=None,
        limit_paadalgal_per_thogupu=None,
        progress_every=0,
    )

    assert summary["counts"]["thirumurai_books"] == 1
    assert summary["counts"]["paadal_thogupugal"] == 1
    assert Path(summary["output_root"], "paadal_thogupugal.jsonl").exists()


def test_tokenizer_keeps_tamil_words() -> None:
    assert tokenize_tamil_text("தோடுடைய செவியன், விடையேறி!") == [
        "தோடுடைய",
        "செவியன்",
        "விடையேறி",
    ]


def test_parse_corpus_filter_accepts_numbers_and_ids() -> None:
    assert parse_corpus_filter("1, thirumurai_05") == {"thirumurai_01", "thirumurai_05"}


def test_fetch_attempts_keep_logical_url_and_add_official_variants() -> None:
    url = "https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529"

    attempts = fetch_attempts(url)

    assert [attempt.name for attempt in attempts] == [
        "default",
        "browser_headers",
        "ipv4_http10",
        "tls12",
        "plain_http",
    ]
    assert attempts[0].url == url
    assert attempts[-1].url == "http://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529"


def test_slet_referer_uses_matching_left_frame() -> None:
    assert (
        slet_referer("https://www.tamilvu.org/slet/l4150/l4150uri.jsp?song_no=1743")
        == "https://www.tamilvu.org/slet/l4150/l4150lft.jsp"
    )


def test_http_variant_only_rewrites_tamilvu_https() -> None:
    assert http_variant("https://www.tamilvu.org/slet/l4110/x.jsp") == "http://www.tamilvu.org/slet/l4110/x.jsp"
    assert http_variant("https://example.org/slet/l4110/x.jsp") == "https://example.org/slet/l4110/x.jsp"
