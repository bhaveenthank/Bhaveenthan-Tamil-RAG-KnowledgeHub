from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tvu_scraper.classify import classify_url
from tvu_scraper.models import DiscoveredLink


def parse_links(source_url: str, html: str) -> list[DiscoveredLink]:
    soup = BeautifulSoup(html, "lxml")
    links: list[DiscoveredLink] = []
    for anchor in soup.find_all("a", href=True):
        url = urljoin(source_url, anchor["href"])
        text = " ".join(anchor.get_text(" ", strip=True).split())
        links.append(
            DiscoveredLink(
                url=url,
                text=text,
                source_url=source_url,
                page_type_hint=classify_url(url),
            )
        )
    return links


def parse_frame_sources(source_url: str, html: str) -> list[DiscoveredLink]:
    soup = BeautifulSoup(html, "lxml")
    frames: list[DiscoveredLink] = []
    for frame in soup.find_all("frame", src=True):
        url = urljoin(source_url, frame["src"])
        name = frame.get("name", "")
        frames.append(
            DiscoveredLink(
                url=url,
                text=name,
                source_url=source_url,
                page_type_hint=classify_url(url),
                relation="frame",
            )
        )
    return frames

