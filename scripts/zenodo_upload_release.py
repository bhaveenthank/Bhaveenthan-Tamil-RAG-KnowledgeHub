from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_RELEASE_ROOT = Path("data/releases/irandaam-thirumurai-v1")
DEFAULT_METADATA = DEFAULT_RELEASE_ROOT / "zenodo_metadata.json"


def request_json(url: str, token: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Zenodo API error {error.code} for {url}: {body}") from error


def upload_file(bucket_url: str, token: str, path: Path) -> None:
    file_url = f"{bucket_url}/{quote(path.name)}"
    data = path.read_bytes()
    request = Request(
        file_url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        },
        method="PUT",
    )
    try:
        with urlopen(request) as response:
            if response.status not in {200, 201}:
                raise RuntimeError(f"unexpected upload status {response.status} for {path}")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Zenodo upload error {error.code} for {path}: {body}") from error


def release_files(root: Path) -> list[Path]:
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    return [root / file_name for file_name in manifest["files"] if file_name != "corpus_manifest.json"] + [
        root / "corpus_manifest.json",
        root / "corpus_checksum.sha256",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a Zenodo draft for the Irandaam Thirumurai v1 release.")
    parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--api-base", default="https://zenodo.org/api")
    parser.add_argument("--publish", action="store_true", help="Publish the deposition after upload. Use only after final review.")
    parser.add_argument("--dry-run", action="store_true", help="List files and metadata without contacting Zenodo.")
    args = parser.parse_args(argv)

    token = os.environ.get("ZENODO_ACCESS_TOKEN")
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    files = release_files(args.release_root)

    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise SystemExit(f"missing release files: {missing}")

    if args.dry_run:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print("Files:")
        for path in files:
            print(f"- {path} ({path.stat().st_size} bytes)")
        return 0

    if not token:
        raise SystemExit("ZENODO_ACCESS_TOKEN is not set. Create a Zenodo token with deposit:write scope.")

    deposition = request_json(
        f"{args.api_base}/deposit/depositions",
        token,
        method="POST",
        payload={"metadata": {**metadata["metadata"], "prereserve_doi": True}},
    )
    deposition_id = deposition["id"]
    bucket_url = deposition["links"]["bucket"]

    for path in files:
        print(f"uploading {path.name}", file=sys.stderr)
        upload_file(bucket_url, token, path)

    updated = request_json(
        f"{args.api_base}/deposit/depositions/{deposition_id}",
        token,
        method="PUT",
        payload=metadata,
    )

    doi = updated.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    html = updated.get("links", {}).get("html")
    print(json.dumps({"deposition_id": deposition_id, "reserved_doi": doi, "draft_url": html}, indent=2))

    if args.publish:
        request_json(
            f"{args.api_base}/deposit/depositions/{deposition_id}/actions/publish",
            token,
            method="POST",
        )
        print("Published deposition. Check Zenodo for the final DOI URL.", file=sys.stderr)
    else:
        print("Draft created but not published. Review rights/access language before publishing.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

