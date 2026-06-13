from __future__ import annotations

from pathlib import Path

package_dir = Path(__file__).resolve().parent
repo_root = package_dir.parents[1]
shared_package_dir = repo_root / "shared/tvu-common/src/tvu_common"

__path__ = [str(package_dir)]
if shared_package_dir.is_dir():
    __path__.append(str(shared_package_dir))

from tvu_common.artifacts import jsonl_text, load_json, load_jsonl, write_once
from tvu_common.checksums import sha256_file, sha256_text
from tvu_common.snapshot import fetch_html, save_snapshot, snapshot_filename
from tvu_common.unicode import normalize_tamil_text, tamil_ratio
from tvu_common.urls import is_internal_tamilvu_url

__all__ = [
    "fetch_html",
    "is_internal_tamilvu_url",
    "jsonl_text",
    "load_json",
    "load_jsonl",
    "normalize_tamil_text",
    "save_snapshot",
    "sha256_file",
    "sha256_text",
    "snapshot_filename",
    "tamil_ratio",
    "write_once",
]
