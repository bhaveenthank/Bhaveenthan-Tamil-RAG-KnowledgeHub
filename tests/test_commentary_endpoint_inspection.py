from bs4 import BeautifulSoup

from inspector.inspect_commentary_endpoint import (
    extract_labels,
    extract_query_params,
    extract_headings,
    extract_text_blocks,
    inspect_html,
)


SOURCE_URL = "https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664"


def test_commentary_heading_detection() -> None:
    soup = BeautifulSoup("<h2>பொழிப்புரை</h2><b>குறிப்புரை</b>", "lxml")

    headings = extract_headings(soup)

    assert [heading.text for heading in headings] == ["பொழிப்புரை", "குறிப்புரை"]


def test_tamil_heavy_block_detection() -> None:
    soup = BeautifulSoup("<div>இது பாடலுக்கான பொழிப்புரை விளக்கம் ஆகும்.</div>", "lxml")

    blocks = extract_text_blocks(soup)

    assert len(blocks) == 1
    assert blocks[0].tamil_chars > 10


def test_url_parameter_extraction() -> None:
    params = extract_query_params(SOURCE_URL)

    assert params["song_no"] == ["1470"]
    assert params["book_id"] == ["110"]
    assert params["head_id"] == ["60"]
    assert params["sub_id"] == ["1664"]


def test_visible_text_block_extraction() -> None:
    soup = BeautifulSoup(
        """
        <table>
          <tr><td>பாடல்</td><td>செந்நெல் அம் கழனி...</td></tr>
          <tr><td>பொழிப்புரை</td><td>இங்கு பாடலின் பொருள் விளக்கப்படுகிறது.</td></tr>
        </table>
        """,
        "lxml",
    )

    blocks = extract_text_blocks(soup)

    assert any("பாடல்" in block.text for block in blocks)
    assert any("பொழிப்புரை" in block.text for block in blocks)


def test_label_detection_for_pozhippurai_and_kurippurai() -> None:
    html = "பாடல் உரை பொழிப்புரை குறிப்புரை குறிப்புரை"

    labels = {label.label: label.count for label in extract_labels(html)}

    assert labels["பாடல்"] == 1
    assert labels["உரை"] >= 1
    assert labels["பொழிப்புரை"] == 1
    assert labels["குறிப்புரை"] == 2


def test_inspect_html_static_extractability() -> None:
    html = """
    <html>
      <head><title>உரை</title></head>
      <body>
        <h2>பொழிப்புரை</h2>
        <table>
          <tr><td>பாடல்</td><td>செந்நெல் அம் கழனி</td></tr>
          <tr><td>குறிப்புரை</td><td>சொல் விளக்கம் இங்கு உள்ளது.</td></tr>
        </table>
        <a href="javascript:window.close()">மூடு</a>
      </body>
    </html>
    """

    inspection = inspect_html(SOURCE_URL, html, "fixture.html")

    assert inspection.title == "உரை"
    assert inspection.query_params["song_no"] == ["1470"]
    assert inspection.extractable_static is True
    assert len(inspection.links) == 1

