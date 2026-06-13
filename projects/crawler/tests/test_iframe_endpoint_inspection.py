from bs4 import BeautifulSoup

from inspector.inspect_iframe_endpoints import (
    extract_content_elements,
    extract_forms,
    extract_frames,
    extract_links,
    extract_scripts,
    inspect_html,
)


SOURCE_URL = "https://www.tamilvu.org/slet/l4120/l4120lft.jsp"


def test_link_and_onclick_extraction() -> None:
    soup = BeautifulSoup(
        """
        <a href="../../ta/library-l4100-html-l4120003-135795?renderframe=simple"
           onclick="parent.right.location=this.href">திருப்பூந்தராய் - வினா உரை - இந்தளம்</a>
        """,
        "lxml",
    )

    links = extract_links(SOURCE_URL, soup)

    assert len(links) == 1
    assert links[0].text.startswith("திருப்பூந்தராய்")
    assert "renderframe=simple" in links[0].href
    assert links[0].onclick == "parent.right.location=this.href"


def test_frame_endpoint_parsing() -> None:
    soup = BeautifulSoup('<frame name="right" src="/ta/example?renderframe=simple">', "lxml")

    frames = extract_frames(SOURCE_URL, soup)

    assert len(frames) == 1
    assert frames[0].tag == "frame"
    assert frames[0].name == "right"
    assert frames[0].src == "https://www.tamilvu.org/ta/example?renderframe=simple"


def test_form_extraction() -> None:
    soup = BeautifulSoup('<form method="post" action="/ta/search" id="search-form" name="q"></form>', "lxml")

    forms = extract_forms(SOURCE_URL, soup)

    assert len(forms) == 1
    assert forms[0].method == "post"
    assert forms[0].action == "https://www.tamilvu.org/ta/search"
    assert forms[0].id == "search-form"


def test_script_extraction() -> None:
    soup = BeautifulSoup('<script src="/library/js/l0100mnu.js"></script><script>load()</script>', "lxml")

    scripts = extract_scripts(SOURCE_URL, soup)

    assert len(scripts) == 2
    assert scripts[0].src == "https://www.tamilvu.org/library/js/l0100mnu.js"
    assert scripts[1].inline_chars == len("load()")


def test_tamil_heavy_element_detection() -> None:
    soup = BeautifulSoup(
        """
        <table>
          <tr><td>திருப்பூந்தராய் - வினா உரை - இந்தளம்</td></tr>
          <tr><td>abc</td></tr>
        </table>
        <div class="content">பொழிப்புரை குறிப்புரை பாடல் வரிகள்</div>
        """,
        "lxml",
    )

    elements = extract_content_elements(soup)

    assert any(element.tag == "tr" and "திருப்பூந்தராய்" in element.text for element in elements)
    assert any(element.tag == "div" and "பொழிப்புரை" in element.text for element in elements)


def test_inspect_html_keyword_and_counts() -> None:
    html = """
    <html>
      <head><title>Frame</title></head>
      <body>
        <a href="/ta/x" onclick="go()">திருப்பூந்தராய் - வினா உரை - இந்தளம்</a>
        <form action="/ta/search"></form>
        <iframe src="/ta/y"></iframe>
        <script src="/library/js/l0100mnu.js"></script>
        <p>பொழிப்புரை குறிப்புரை</p>
      </body>
    </html>
    """

    inspection = inspect_html(SOURCE_URL, html, "fixture.html")

    assert inspection.title == "Frame"
    assert len(inspection.links) == 1
    assert len(inspection.forms) == 1
    assert len(inspection.frames) == 1
    assert len(inspection.scripts) == 1
    assert any(keyword.keyword == "இந்தளம்" and keyword.count == 1 for keyword in inspection.keywords)

