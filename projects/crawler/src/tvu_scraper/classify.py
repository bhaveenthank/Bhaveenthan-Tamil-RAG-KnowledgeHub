from __future__ import annotations

from urllib.parse import urlparse

from tvu_scraper.models import PageType


def classify_url(url: str) -> PageType:
    parsed = urlparse(url)
    path = parsed.path
    query = parsed.query

    if "format=simple" in query and (path.startswith("/node/") or "/ta/library-" in path):
        return PageType.DRUPAL_SIMPLE_NODE
    if path.startswith("/slet/") and path.endswith(".jsp"):
        return PageType.SLET_TREE
    if path.startswith("/library/") and path.endswith((".htm", ".html")):
        return PageType.LEGACY_HTML
    if path.startswith("/library/") and not path.endswith((".htm", ".html")):
        return PageType.ASSET
    if path == "/ta/library-libcontnt-273141":
        return PageType.MODERN_CATALOG
    if path.startswith("/ta/library-"):
        return PageType.MODERN_WRAPPER
    return PageType.UNKNOWN


def classify_html(url: str, html: str) -> PageType:
    initial = classify_url(url)
    lowered = html[:5000].lower()
    if "<frameset" in lowered:
        return PageType.LEGACY_FRAMESET
    return initial

