from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from tvu_common.checksums import sha256_text

USER_AGENT = "tvu-corpus-research/0.1 (+student research; polite allowlist inspection)"


def snapshot_filename(url: str) -> str:
    parsed = urlparse(url)
    stem = re.sub(r"[^A-Za-z0-9]+", "-", parsed.path.strip("/")).strip("-")
    if not stem:
        stem = "root"
    digest = sha256_text(url)[:12]
    return f"{stem}-{digest}.html"


def save_snapshot(url: str, html: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / snapshot_filename(url)
    path.write_text(html, encoding="utf-8")
    return path


def fetch_html(url: str, timeout: int) -> str:
    import requests

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        timeout=timeout,
    )
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text
