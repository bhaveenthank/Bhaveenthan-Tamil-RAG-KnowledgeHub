from tvu_scraper.classify import classify_html, classify_url
from tvu_scraper.models import PageType


def test_classifies_seed_catalog() -> None:
    assert (
        classify_url("https://www.tamilvu.org/ta/library-libcontnt-273141")
        == PageType.MODERN_CATALOG
    )


def test_classifies_legacy_html() -> None:
    assert (
        classify_url("https://www.tamilvu.org/library/l4100/html/l4100cor.htm")
        == PageType.LEGACY_HTML
    )


def test_classifies_frameset_from_html() -> None:
    html = "<html><frameset cols='25%,*'><frame src='/slet/l1100/l1100lft.jsp'></frameset></html>"
    assert (
        classify_html("https://www.tamilvu.org/library/l1100/html/l1100ind.htm", html)
        == PageType.LEGACY_FRAMESET
    )


def test_classifies_simple_node() -> None:
    assert (
        classify_url("https://www.tamilvu.org/node/67708?format=simple")
        == PageType.DRUPAL_SIMPLE_NODE
    )

