from bs4 import BeautifulSoup

from inspector.inspect_hymn_endpoint import (
    extract_links,
    extract_poem_blocks,
    extract_query_params,
    extract_table_rows,
    extract_text_blocks,
    extract_urai_links,
    inspect_html,
)


SOURCE_URL = "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664"


def test_poem_block_detection() -> None:
    soup = BeautifulSoup(
        """
        <table>
          <tr><td>1.</td><td>வரி ஒன்று<br>வரி இரண்டு<br>வரி மூன்று<br>வரி நான்கு</td></tr>
        </table>
        """,
        "lxml",
    )

    blocks = extract_poem_blocks(soup)

    assert blocks
    assert any(block.line_count >= 3 for block in blocks)


def test_tamil_heavy_block_detection() -> None:
    soup = BeautifulSoup("<div>திருப்பூந்தராய் பாடல் வரிகள் இங்கு உள்ளன</div>", "lxml")

    blocks = extract_text_blocks(soup)

    assert len(blocks) == 1
    assert blocks[0].tamil_chars > 10


def test_urai_link_detection() -> None:
    soup = BeautifulSoup(
        '<a href="l4120urai.jsp?subid=1664&song=1" title="உரை">உரை</a>',
        "lxml",
    )

    links = extract_links(SOURCE_URL, soup)
    urai_links = extract_urai_links(links)

    assert len(urai_links) == 1
    assert "l4120urai.jsp" in urai_links[0].href


def test_query_parameter_extraction() -> None:
    params = extract_query_params(SOURCE_URL)

    assert params == {"subid": ["1664"]}


def test_table_row_extraction() -> None:
    soup = BeautifulSoup(
        """
        <table>
          <tr><td>திருப்பூந்தராய்</td><td>இந்தளம்</td></tr>
          <tr><td>abc</td></tr>
        </table>
        """,
        "lxml",
    )

    rows = extract_table_rows(soup)

    assert len(rows) == 1
    assert rows[0].cells == ["திருப்பூந்தராய்", "இந்தளம்"]


def test_inspect_html_summary() -> None:
    html = """
    <html>
      <head><title>திருப்பூந்தராய்</title></head>
      <body>
        <table><tr><td>1.</td><td>வரி ஒன்று<br>வரி இரண்டு<br>வரி மூன்று<br>வரி நான்கு</td></tr></table>
        <a href="l4120urai.jsp?subid=1664&song=1">உரை</a>
        <div style="display:none">பொழிப்புரை குறிப்புரை</div>
      </body>
    </html>
    """

    inspection = inspect_html(SOURCE_URL, html, "fixture.html")

    assert inspection.title == "திருப்பூந்தராய்"
    assert inspection.query_params["subid"] == ["1664"]
    assert inspection.poem_blocks
    assert len(inspection.urai_links) == 1
    assert len(inspection.hidden_content) == 1

