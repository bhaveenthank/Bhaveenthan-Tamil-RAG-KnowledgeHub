from inspector.site_inspector import (
    classify_url_pattern,
    extract_page_info,
    snapshot_filename,
)


def test_classify_manual_inspection_urls() -> None:
    assert (
        classify_url_pattern("https://www.tamilvu.org/ta/library-libcontnt-273141")
        == "main_library_category"
    )
    assert (
        classify_url_pattern("https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793")
        == "thirumurai_hymn_list_modern_wrapper"
    )


def test_extract_page_info_links_and_urai_controls() -> None:
    html = """
    <html>
      <head><title>இரண்டாம் திருமுறை</title></head>
      <body>
        <a href="/ta/library-l4100-html-l4100cor-135660">சைவம்</a>
        <a href="https://example.com/outside">outside</a>
        <a href="#urai1" title="உரை">உரை</a>
        <button aria-label="குறிப்புரை">?</button>
        <p>திருப்பூந்தராய் பாடல் வரிகள்</p>
      </body>
    </html>
    """

    page = extract_page_info("https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793", html)

    assert page.title == "இரண்டாம் திருமுறை"
    assert len(page.internal_links) == 2
    assert page.internal_links[0].text == "சைவம்"
    assert page.internal_links[0].pattern == "subcategory_modern_wrapper"
    assert len(page.urai_controls) == 2
    assert page.tamil_text_length > 0


def test_snapshot_filename_is_stable_and_html() -> None:
    first = snapshot_filename("https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793")
    second = snapshot_filename("https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793")

    assert first == second
    assert first.endswith(".html")

