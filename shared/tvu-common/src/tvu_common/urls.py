from __future__ import annotations

from urllib.parse import urlparse

TAMILVU_HOST = "www.tamilvu.org"


def is_internal_tamilvu_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in {"", TAMILVU_HOST}
