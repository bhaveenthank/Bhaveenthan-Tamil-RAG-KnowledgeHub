from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspector.site_inspector import USER_AGENT, fetch_html, save_snapshot, snapshot_filename

FRAME_URLS = [
    "https://www.tamilvu.org/slet/l4120/l4120lft.jsp",
    "https://www.tamilvu.org/ta/library-l4100-html-l4120003-135795?renderframe=simple",
]
DEFAULT_OUTPUT_DIR = Path("data/raw/inspection/frames")
DEFAULT_REPORT_PATH = Path("reports/iframe-endpoint-inspection.md")
TAMILVU_HOST = "www.tamilvu.org"
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
KEYWORDS = ["திருப்பூந்தராய்", "உரை", "பொழிப்புரை", "குறிப்புரை", "இந்தளம்"]


@dataclass(slots=True)
class LinkFinding:
    text: str
    href: str
    onclick: str | None


@dataclass(slots=True)
class FrameFinding:
    tag: str
    src: str
    id: str
    name: str
    classes: str


@dataclass(slots=True)
class FormFinding:
    method: str
    action: str
    id: str
    name: str


@dataclass(slots=True)
class ScriptFinding:
    src: str | None
    inline_chars: int


@dataclass(slots=True)
class KeywordFinding:
    keyword: str
    count: int
    snippets: list[str]


@dataclass(slots=True)
class ContentElement:
    tag: str
    text: str
    tamil_chars: int
    total_chars: int
    id: str
    classes: str


@dataclass(slots=True)
class EndpointInspection:
    url: str
    snapshot_path: str
    title: str
    tamil_text_length: int
    links: list[LinkFinding]
    frames: list[FrameFinding]
    forms: list[FormFinding]
    scripts: list[ScriptFinding]
    keywords: list[KeywordFinding]
    content_elements: list[ContentElement]


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def trim(text: str, limit: int = 180) -> str:
    normalized = normalize_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def attr_string(tag: Tag, attr: str) -> str:
    value = tag.get(attr, "")
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def tamil_char_count(text: str) -> int:
    return len(TAMIL_RE.findall(text))


def is_internal_tamilvu_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in {"", TAMILVU_HOST}


def resolve_url(source_url: str, value: str | None) -> str:
    if not value:
        return ""
    if value.lower().startswith("javascript:"):
        return value
    return urljoin(source_url, value)


def snippet_around(text: str, keyword: str, radius: int = 80) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(keyword) + radius)
    return trim(text[start:end])


def extract_links(source_url: str, soup: BeautifulSoup) -> list[LinkFinding]:
    findings: list[LinkFinding] = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href", "")
        resolved = resolve_url(source_url, href)
        if resolved and not resolved.startswith("javascript:") and not is_internal_tamilvu_url(resolved):
            continue
        findings.append(
            LinkFinding(
                text=trim(anchor.get_text(" ", strip=True)),
                href=resolved,
                onclick=str(anchor.get("onclick")) if anchor.get("onclick") else None,
            )
        )
    return findings


def extract_frames(source_url: str, soup: BeautifulSoup) -> list[FrameFinding]:
    findings: list[FrameFinding] = []
    for tag in soup.find_all(["iframe", "frame"]):
        findings.append(
            FrameFinding(
                tag=tag.name or "",
                src=resolve_url(source_url, tag.get("src", "")),
                id=attr_string(tag, "id"),
                name=attr_string(tag, "name"),
                classes=attr_string(tag, "class"),
            )
        )
    return findings


def extract_forms(source_url: str, soup: BeautifulSoup) -> list[FormFinding]:
    findings: list[FormFinding] = []
    for form in soup.find_all("form"):
        findings.append(
            FormFinding(
                method=attr_string(form, "method").lower() or "get",
                action=resolve_url(source_url, form.get("action", "")),
                id=attr_string(form, "id"),
                name=attr_string(form, "name"),
            )
        )
    return findings


def extract_scripts(source_url: str, soup: BeautifulSoup) -> list[ScriptFinding]:
    findings: list[ScriptFinding] = []
    for script in soup.find_all("script"):
        src = script.get("src")
        inline_text = script.string or script.get_text(" ", strip=True) or ""
        findings.append(
            ScriptFinding(
                src=resolve_url(source_url, src) if src else None,
                inline_chars=len(inline_text),
            )
        )
    return findings


def extract_keywords(html: str) -> list[KeywordFinding]:
    findings: list[KeywordFinding] = []
    for keyword in KEYWORDS:
        count = html.count(keyword)
        snippets: list[str] = []
        start = 0
        while len(snippets) < 3:
            index = html.find(keyword, start)
            if index < 0:
                break
            snippets.append(snippet_around(html[index:], keyword))
            start = index + len(keyword)
        findings.append(KeywordFinding(keyword=keyword, count=count, snippets=snippets))
    return findings


def extract_content_elements(soup: BeautifulSoup, limit: int = 80) -> list[ContentElement]:
    candidates: list[ContentElement] = []
    for tag in soup.find_all(["tr", "div", "a", "p", "td", "li"]):
        text = trim(tag.get_text(" ", strip=True), limit=220)
        if not text:
            continue
        tamil_chars = tamil_char_count(text)
        total_chars = len(text)
        if tamil_chars < 4:
            continue
        tamil_ratio = tamil_chars / max(total_chars, 1)
        if tamil_chars < 12 and tamil_ratio < 0.4:
            continue
        candidates.append(
            ContentElement(
                tag=tag.name or "",
                text=text,
                tamil_chars=tamil_chars,
                total_chars=total_chars,
                id=attr_string(tag, "id"),
                classes=attr_string(tag, "class"),
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def inspect_html(url: str, html: str, snapshot_path: str) -> EndpointInspection:
    soup = BeautifulSoup(html, "lxml")
    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    visible_text = soup.get_text("\n", strip=True)
    return EndpointInspection(
        url=url,
        snapshot_path=snapshot_path,
        title=title,
        tamil_text_length=tamil_char_count(visible_text),
        links=extract_links(url, soup),
        frames=extract_frames(url, soup),
        forms=extract_forms(url, soup),
        scripts=extract_scripts(url, soup),
        keywords=extract_keywords(html),
        content_elements=extract_content_elements(soup),
    )


def fetch_and_inspect(urls: list[str], output_dir: Path, delay: float, timeout: int) -> list[EndpointInspection]:
    inspections: list[EndpointInspection] = []
    for index, url in enumerate(urls):
        if not is_internal_tamilvu_url(url):
            raise ValueError(f"Refusing non-TamilVU frame URL: {url}")
        print(f"Inspecting frame endpoint {url}", file=sys.stderr)
        html = fetch_html(url, timeout=timeout)
        snapshot_path = save_snapshot(url, html, output_dir)
        inspections.append(inspect_html(url, html, str(snapshot_path)))
        if index < len(urls) - 1:
            time.sleep(delay)
    return inspections


def markdown_table_cell(value: str | None) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ")


def render_report(inspections: list[EndpointInspection]) -> str:
    lines = [
        "# iframe Endpoint Inspection Report",
        "",
        "This report inspects only the two iframe endpoints discovered from the Thirumurai wrapper.",
        "It does not recursively crawl linked pages.",
        "",
    ]
    for inspection in inspections:
        lines.extend(
            [
                f"## {inspection.title or inspection.url}",
                "",
                f"- URL: `{inspection.url}`",
                f"- Snapshot: `{inspection.snapshot_path}`",
                f"- Rough Tamil text length: `{inspection.tamil_text_length}`",
                f"- Internal links: `{len(inspection.links)}`",
                f"- onclick links: `{sum(1 for link in inspection.links if link.onclick)}`",
                f"- frame/iframe tags: `{len(inspection.frames)}`",
                f"- forms: `{len(inspection.forms)}`",
                f"- scripts: `{len(inspection.scripts)}`",
                "",
                "### Tamil Keyword Matches",
                "",
                "| Keyword | Count | Snippets |",
                "| --- | ---: | --- |",
            ]
        )
        for keyword in inspection.keywords:
            snippets = "<br/>".join(markdown_table_cell(snippet) for snippet in keyword.snippets)
            lines.append(f"| {keyword.keyword} | {keyword.count} | {snippets} |")

        lines.extend(["", "### Links", "", "| Text | Href | onclick |", "| --- | --- | --- |"])
        for link in inspection.links:
            lines.append(
                f"| {markdown_table_cell(link.text) or '(no text)'} | `{markdown_table_cell(link.href)}` | `{markdown_table_cell(link.onclick)}` |"
            )
        if not inspection.links:
            lines.append("| _None._ | | |")

        lines.extend(["", "### Frames", "", "| Tag | ID | Name | Class | Src |", "| --- | --- | --- | --- | --- |"])
        for frame in inspection.frames:
            lines.append(
                f"| `{frame.tag}` | `{markdown_table_cell(frame.id)}` | `{markdown_table_cell(frame.name)}` | `{markdown_table_cell(frame.classes)}` | `{markdown_table_cell(frame.src)}` |"
            )
        if not inspection.frames:
            lines.append("| _None._ | | | | |")

        lines.extend(["", "### Forms", "", "| Method | Action | ID | Name |", "| --- | --- | --- | --- |"])
        for form in inspection.forms:
            lines.append(
                f"| `{form.method}` | `{markdown_table_cell(form.action)}` | `{markdown_table_cell(form.id)}` | `{markdown_table_cell(form.name)}` |"
            )
        if not inspection.forms:
            lines.append("| _None._ | | | |")

        lines.extend(["", "### Scripts", "", "| Src | Inline Chars |", "| --- | ---: |"])
        for script in inspection.scripts:
            lines.append(f"| `{markdown_table_cell(script.src)}` | {script.inline_chars} |")
        if not inspection.scripts:
            lines.append("| _None._ | |")

        lines.extend(
            [
                "",
                "### Possible Content-Bearing Elements",
                "",
                "| Tag | Tamil Chars | Total Chars | ID | Class | Text |",
                "| --- | ---: | ---: | --- | --- | --- |",
            ]
        )
        for element in inspection.content_elements:
            lines.append(
                f"| `{element.tag}` | {element.tamil_chars} | {element.total_chars} | `{markdown_table_cell(element.id)}` | `{markdown_table_cell(element.classes)}` | {markdown_table_cell(element.text)} |"
            )
        if not inspection.content_elements:
            lines.append("| _None._ | | | | | |")
        lines.append("")

    return "\n".join(lines)


def print_links(inspections: list[EndpointInspection]) -> None:
    for inspection in inspections:
        print(f"\n{inspection.url}")
        if not inspection.links:
            print("- No links found.")
            continue
        for link in inspection.links:
            print(f"- text={link.text!r} href={link.href!r} onclick={link.onclick!r}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect TamilVU Thirumurai iframe endpoints")
    parser.add_argument("--url", action="append", dest="urls", help="Frame endpoint URL. Defaults to both discovered endpoints.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--print-links", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    urls = args.urls or FRAME_URLS
    inspections = fetch_and_inspect(urls, args.output_dir, args.delay, args.timeout)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(inspections), encoding="utf-8")
    print(f"Report written to {args.report}")
    if args.print_links:
        print_links(inspections)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

