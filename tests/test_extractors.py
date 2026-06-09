from tvu_scraper.extractors import parse_frame_sources, parse_links


def test_parse_links_resolves_relative_legacy_urls() -> None:
    html = '<a href="../../l41F0/html/l41F0ind.htm">திருப்புகழ்</a>'
    links = parse_links("https://www.tamilvu.org/library/l4100/html/l4100cor.htm", html)

    assert str(links[0].url) == "https://www.tamilvu.org/library/l41F0/html/l41F0ind.htm"
    assert links[0].text == "திருப்புகழ்"


def test_parse_frame_sources() -> None:
    html = """
    <frameset cols="185,*">
      <frame name="left" src="/slet/l4110/l4110lft.jsp">
      <frame name="right" src="l4110ind.htm">
    </frameset>
    """
    frames = parse_frame_sources("https://www.tamilvu.org/library/l4110/html/l4110in2.htm", html)

    assert str(frames[0].url) == "https://www.tamilvu.org/slet/l4110/l4110lft.jsp"
    assert str(frames[1].url) == "https://www.tamilvu.org/library/l4110/html/l4110ind.htm"

