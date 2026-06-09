from inspector.discover_dynamic_content import (
    discover_dynamic_content,
    extract_frames,
    extract_handlers,
    extract_hidden_elements,
    extract_keyword_findings,
)
from bs4 import BeautifulSoup


SOURCE_URL = "https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793"


def test_onclick_and_javascript_href_extraction() -> None:
    soup = BeautifulSoup(
        """
        <a href="javascript:void(0)" onclick="loadHymn('/library/l4120/html/foo.htm')">
          திருப்பூந்தராய் - வினா உரை - இந்தளம்
        </a>
        """,
        "lxml",
    )

    onclicks, javascript_hrefs = extract_handlers(SOURCE_URL, soup)

    assert len(onclicks) == 1
    assert "loadHymn" in (onclicks[0].onclick or "")
    assert len(javascript_hrefs) == 1
    assert javascript_hrefs[0].href == "javascript:void(0)"


def test_iframe_detection() -> None:
    soup = BeautifulSoup(
        '<iframe id="left_top_frame" src="/slet/l4120/l4120lft.jsp" name="left"></iframe>',
        "lxml",
    )

    frames = extract_frames(SOURCE_URL, soup)

    assert len(frames) == 1
    assert frames[0].src == "https://www.tamilvu.org/slet/l4120/l4120lft.jsp"
    assert frames[0].id == "left_top_frame"


def test_tamil_keyword_detection() -> None:
    html = "திருப்பூந்தராய் பாடல் உரை பொழிப்புரை குறிப்புரை"

    findings = {finding.keyword: finding.count for finding in extract_keyword_findings(html)}

    assert findings["திருப்பூந்தராய்"] == 1
    assert findings["உரை"] >= 1
    assert findings["பொழிப்புரை"] == 1
    assert findings["குறிப்புரை"] == 1


def test_hidden_content_detection() -> None:
    soup = BeautifulSoup(
        """
        <div id="commentary" class="urai-panel" style="display:none">பொழிப்புரை</div>
        <section aria-hidden="true">குறிப்புரை</section>
        """,
        "lxml",
    )

    hidden = extract_hidden_elements(soup)

    assert len(hidden) == 2
    assert hidden[0].id == "commentary"
    assert "display:none" in hidden[0].reason


def test_discovery_finds_hymn_candidate_and_keywords() -> None:
    html = """
    <html>
      <script src="/sites/all/themes/tb_sirate/js/left_iframeset.js"></script>
      <iframe src="/slet/l4120/l4120lft.jsp"></iframe>
      <a href="javascript:void(0)" onclick="load('/ta/library-l4100-html-l4120003-135795?renderframe=simple')">
        திருப்பூந்தராய் - வினா உரை - இந்தளம்
      </a>
      <div id="right_content_panel" style="visibility:hidden">குறிப்புரை</div>
    </html>
    """

    discovery = discover_dynamic_content(SOURCE_URL, html, "fixture.html")

    assert len(discovery.frames) == 1
    assert len(discovery.handlers) == 1
    assert len(discovery.javascript_hrefs) == 1
    assert discovery.hymn_candidates[0].text.startswith("திருப்பூந்தராய்")
    assert any(finding.keyword == "குறிப்புரை" and finding.count == 1 for finding in discovery.keywords)

