from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

USER_AGENT = "tvu-corpus-site-inspector/0.1 (+student research; polite allowlist inspection)"
DEFAULT_OUTPUT_DIR = Path("data/raw/inspection")
DEFAULT_REPORT_PATH = Path("reports/site-inspection-report.md")
TAMILVU_HOST = "www.tamilvu.org"
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
URAI_RE = re.compile("உரை|பொழிப்புரை|குறிப்புரை")

DEFAULT_ALLOWLIST = [
    "https://www.tamilvu.org/ta/library-libcontnt-273141",
    "https://www.tamilvu.org/ta/library-l4100-html-l4100cor-135660",
    "https://www.tamilvu.org/ta/library-l4100-html-l4100ind-135661",
    "https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793",
]


@dataclass(slots=True)
class LinkInfo:
    text: str
    url: str
    pattern: str


@dataclass(slots=True)
class UraiControl:
    tag: str
    text: str
    href: str | None
    attributes: dict[str, str]


@dataclass(slots=True)
class PageInspection:
    url: str
    title: str
    snapshot_path: str | None
    tamil_text_length: int
    internal_links: list[LinkInfo]
    urai_controls: list[UraiControl]


def is_internal_tamilvu_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in {"", TAMILVU_HOST}


def classify_url_pattern(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    query = parsed.query

    if path == "/ta/library-libcontnt-273141":
        return "main_library_category"
    if path.startswith("/ta/library-") and "l4100cor" in path:
        return "subcategory_modern_wrapper"
    if path.startswith("/ta/library-") and "l4100ind" in path:
        return "collection_index_modern_wrapper"
    if path.startswith("/ta/library-") and "l4120001" in path:
        return "thirumurai_hymn_list_modern_wrapper"
    if path.startswith("/ta/library-"):
        return "modern_library_wrapper"
    if path.startswith("/library/") and path.endswith((".htm", ".html")):
        return "legacy_html"
    if path.startswith("/slet/"):
        return "slet_or_jsp"
    if path.startswith("/node/") or "format=simple" in query:
        return "drupal_simple_node"
    return "other_internal"


def tamil_text_length(text: str) -> int:
    return len(TAMIL_RE.findall(text))


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def extract_page_info(url: str, html: str, snapshot_path: str | None = None) -> PageInspection:
    soup = BeautifulSoup(html, "lxml")
    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""

    links: list[LinkInfo] = []
    seen: set[tuple[str, str]] = set()
    for anchor in soup.find_all("a", href=True):
        absolute_url = urljoin(url, anchor["href"])
        if not is_internal_tamilvu_url(absolute_url):
            continue
        text = normalize_text(anchor.get_text(" ", strip=True))
        key = (absolute_url, text)
        if key in seen:
            continue
        seen.add(key)
        links.append(
            LinkInfo(
                text=text,
                url=absolute_url,
                pattern=classify_url_pattern(absolute_url),
            )
        )

    urai_controls = extract_urai_controls(url, soup)
    visible_text = soup.get_text("\n", strip=True)

    return PageInspection(
        url=url,
        title=title,
        snapshot_path=snapshot_path,
        tamil_text_length=tamil_text_length(visible_text),
        internal_links=links,
        urai_controls=urai_controls,
    )


def extract_urai_controls(source_url: str, soup: BeautifulSoup) -> list[UraiControl]:
    controls: list[UraiControl] = []
    candidate_tags = ["a", "button", "input", "img", "span"]
    for tag in soup.find_all(candidate_tags):
        text_parts = [
            tag.get_text(" ", strip=True),
            tag.get("title", ""),
            tag.get("alt", ""),
            tag.get("value", ""),
            tag.get("aria-label", ""),
        ]
        combined_text = normalize_text(" ".join(part for part in text_parts if part))
        href = tag.get("href")
        absolute_href = urljoin(source_url, href) if href else None
        attr_text = " ".join(str(value) for value in tag.attrs.values())
        if not URAI_RE.search(combined_text) and not URAI_RE.search(attr_text):
            continue

        simple_attrs: dict[str, str] = {}
        for key, value in tag.attrs.items():
            if isinstance(value, list):
                simple_attrs[key] = " ".join(str(item) for item in value)
            else:
                simple_attrs[key] = str(value)

        controls.append(
            UraiControl(
                tag=tag.name or "",
                text=combined_text,
                href=absolute_href,
                attributes=simple_attrs,
            )
        )
    return controls


def snapshot_filename(url: str) -> str:
    parsed = urlparse(url)
    stem = re.sub(r"[^A-Za-z0-9]+", "-", parsed.path.strip("/")).strip("-")
    if not stem:
        stem = "root"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
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


def render_report(inspections: Iterable[PageInspection]) -> str:
    lines = [
        "# TamilVU Site Inspection Report",
        "",
        "This report is generated by `src/inspector/site_inspector.py`.",
        "It is allowlist-only and does not recursively crawl TamilVU.",
        "",
    ]

    for page in inspections:
        lines.extend(
            [
                f"## {page.title or page.url}",
                "",
                f"- URL: `{page.url}`",
                f"- Snapshot: `{page.snapshot_path or 'not saved'}`",
                f"- Rough Tamil text length: `{page.tamil_text_length}`",
                f"- Internal TamilVU links: `{len(page.internal_links)}`",
                f"- Possible உரை controls: `{len(page.urai_controls)}`",
                "",
                "### Internal Links",
                "",
                "| Text | Pattern | URL |",
                "| --- | --- | --- |",
            ]
        )
        for link in page.internal_links:
            text = link.text.replace("|", "\\|") or "(no text)"
            lines.append(f"| {text} | `{link.pattern}` | `{link.url}` |")

        lines.extend(["", "### Possible உரை Controls", ""])
        if not page.urai_controls:
            lines.append("_None detected._")
        else:
            lines.extend(["| Tag | Text | Href |", "| --- | --- | --- |"])
            for control in page.urai_controls:
                text = control.text.replace("|", "\\|") or "(no text)"
                href = control.href or ""
                lines.append(f"| `{control.tag}` | {text} | `{href}` |")
        lines.append("")

    return "\n".join(lines)


def inspect_urls(
    urls: list[str],
    output_dir: Path,
    report_path: Path,
    delay_seconds: float,
    timeout: int,
    dry_run: bool,
) -> list[PageInspection]:
    inspections: list[PageInspection] = []

    if dry_run:
        for url in urls:
            print(f"DRY RUN: would inspect {url} ({classify_url_pattern(url)})")
        return inspections

    for index, url in enumerate(urls):
        if not is_internal_tamilvu_url(url):
            raise ValueError(f"Refusing non-TamilVU URL outside allowlist scope: {url}")
        print(f"Inspecting {url}", file=sys.stderr)
        html = fetch_html(url, timeout=timeout)
        snapshot_path = save_snapshot(url, html, output_dir)
        inspection = extract_page_info(url, html, snapshot_path=str(snapshot_path))
        inspections.append(inspection)
        print(
            f"- title={inspection.title!r} tamil_chars={inspection.tamil_text_length} "
            f"links={len(inspection.internal_links)} urai={len(inspection.urai_controls)}"
        )
        if index < len(urls) - 1:
            time.sleep(delay_seconds)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(inspections), encoding="utf-8")
    print(f"Report written to {report_path}")
    return inspections


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Allowlist-only TamilVU site inspector")
    parser.add_argument(
        "--url",
        action="append",
        dest="urls",
        help="TamilVU URL to inspect. Can be passed multiple times. Defaults to manual inspection allowlist.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests in seconds")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print allowlist only; do not fetch")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    urls = args.urls or DEFAULT_ALLOWLIST
    inspect_urls(
        urls=urls,
        output_dir=args.output_dir,
        report_path=args.report,
        delay_seconds=args.delay,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
