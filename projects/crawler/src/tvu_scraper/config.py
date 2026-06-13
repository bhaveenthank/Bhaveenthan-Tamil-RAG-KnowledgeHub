from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class SiteConfig:
    name: str
    root_url: str
    seed_url: str
    user_agent: str


@dataclass(slots=True)
class CrawlConfig:
    enabled: bool
    politeness_delay_seconds: float
    timeout_seconds: int
    max_retries: int
    max_concurrency: int
    obey_robots_txt: bool
    allowed_hosts: list[str]
    allowed_path_prefixes: list[str]
    deny_extensions: list[str]


@dataclass(slots=True)
class StorageConfig:
    raw_dir: str
    processed_dir: str
    index_dir: str
    manifest_db: str


@dataclass(slots=True)
class ExtractionConfig:
    preserve_html: bool
    normalize_unicode: str
    keep_navigation_text: bool
    capture_images: bool
    capture_tables: bool
    min_tamil_ratio: float


@dataclass(slots=True)
class IndexingConfig:
    chunk_strategy: str
    target_chunk_chars: int
    chunk_overlap_chars: int
    vector_store: str
    lexical_store: str


@dataclass(slots=True)
class AppConfig:
    site: SiteConfig
    crawl: CrawlConfig
    storage: StorageConfig
    extraction: ExtractionConfig
    indexing: IndexingConfig


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return AppConfig(
        site=SiteConfig(**data["site"]),
        crawl=CrawlConfig(**data["crawl"]),
        storage=StorageConfig(**data["storage"]),
        extraction=ExtractionConfig(**data["extraction"]),
        indexing=IndexingConfig(**data["indexing"]),
    )
