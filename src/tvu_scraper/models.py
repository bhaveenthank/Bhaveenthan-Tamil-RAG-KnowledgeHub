from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class PageType(StrEnum):
    MODERN_CATALOG = "modern_catalog"
    MODERN_WRAPPER = "modern_wrapper"
    LEGACY_HTML = "legacy_html"
    LEGACY_FRAMESET = "legacy_frameset"
    SLET_TREE = "slet_tree"
    DRUPAL_SIMPLE_NODE = "drupal_simple_node"
    ASSET = "asset"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class FetchSnapshot:
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content_sha256: str
    fetched_at: datetime
    detected_encoding: str | None = None
    parent_url: str | None = None
    crawl_reason: str | None = None


@dataclass(slots=True)
class DiscoveredLink:
    url: str
    source_url: str
    text: str = ""
    page_type_hint: PageType = PageType.UNKNOWN
    relation: str = "link"


@dataclass(slots=True)
class QualityInfo:
    parser: str
    confidence: float
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CorpusRecord:
    id: str
    type: str
    text: str
    source_url: str
    quality: QualityInfo
    title: str | None = None
    html: str | None = None
    language: str = "ta"
    source_path: list[str] = field(default_factory=list)
    work: str | None = None
    section: str | None = None
    authors: list[str] = field(default_factory=list)
    commentary_authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
