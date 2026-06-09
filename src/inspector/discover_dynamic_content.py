from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspector.site_inspector import USER_AGENT, fetch_html, save_snapshot, snapshot_filename

TARGET_URL = "https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793"
DEFAULT_SNAPSHOT_DIR = Path("data/raw/inspection")
DEFAULT_REPORT_PATH = Path("reports/dynamic-content-discovery.md")

KEYWORDS = ["திருப்பூந்தராய்", "உரை", "பொழிப்புரை", "குறிப்புரை"]
PANEL_RE = re.compile(r"(content|panel|frame|iframe|right|left|tab|urai|உரை)", re.IGNORECASE)
HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.IGNORECASE)
URL_FRAGMENT_RE = re.compile(
    r"""(?:
        https?://[^\s"'<>]+
        |/[A-Za-z0-9_./?=&:%+-]+
        |[A-Za-z0-9_./-]+\.(?:jsp|html?|js|php)(?:\?[A-Za-z0-9_./?=&:%+-]+)?
    )""",
    re.VERBOSE,
)


@dataclass(slots=True)
class ScriptFinding:
    src: str | None
    inline_chars: int
    snippet: str


@dataclass(slots=True)
class FrameFinding:
    tag: str
    src: str
    id: str
    name: str
    classes: str


@dataclass(slots=True)
class HandlerFinding:
    tag: str
    text: str
    href: str | None
    onclick: str | None


@dataclass(slots=True)
class KeywordFinding:
    keyword: str
    count: int
    snippets: list[str]


@dataclass(slots=True)
class HiddenFinding:
    tag: str
    id: str
    classes: str
    reason: str
    text_snippet: str


@dataclass(slots=True)
class PanelFinding:
    tag: str
    id: str
    classes: str
    text_snippet: str


@dataclass(slots=True)
class HymnCandidate:
    text: str
    href: str | None
    onclick: str | None
    nearby_urls: list[str]


@dataclass(slots=True)
class DynamicDiscovery:
    source_url: str
    source_path: str
    scripts: list[ScriptFinding]
    frames: list[FrameFinding]
    handlers: list[HandlerFinding]
    javascript_hrefs: list[HandlerFinding]
    keywords: list[KeywordFinding]
    hidden_elements: list[HiddenFinding]
    panels: list[PanelFinding]
    hymn_candidates: list[HymnCandidate]


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def snippet_around(text: str, needle: str, radius: int = 80) -> str:
    index = text.find(needle)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(needle) + radius)
    return normalize_text(text[start:end])


def trim(value: str, limit: int = 180) -> str:
    normalized = normalize_text(value)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def attr_string(tag: Tag, attr: str) -> str:
    value = tag.get(attr, "")
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def find_snapshot_for_url(url: str, snapshot_dir: Path) -> Path | None:
    expected = snapshot_dir / snapshot_filename(url)
    if expected.exists():
        return expected
    matches = sorted(snapshot_dir.glob("*l4120001*.html"))
    return matches[0] if matches else None


def load_html(url: str, snapshot_dir: Path, fetch: bool, timeout: int) -> tuple[str, Path]:
    snapshot = find_snapshot_for_url(url, snapshot_dir)
    if snapshot and not fetch:
        return snapshot.read_text(encoding="utf-8"), snapshot

    if not fetch:
        raise FileNotFoundError(
            f"No saved snapshot found for {url}. Run site_inspector first or pass --fetch."
        )

    html = fetch_html(url, timeout=timeout)
    snapshot_path = save_snapshot(url, html, snapshot_dir)
    return html, snapshot_path


def extract_scripts(source_url: str, soup: BeautifulSoup) -> list[ScriptFinding]:
    findings: list[ScriptFinding] = []
    for script in soup.find_all("script"):
        src = script.get("src")
        absolute_src = urljoin(source_url, src) if src else None
        inline_text = script.string or script.get_text(" ", strip=True) or ""
        findings.append(
            ScriptFinding(
                src=absolute_src,
                inline_chars=len(inline_text),
                snippet=trim(inline_text),
            )
        )
    return findings


def extract_frames(source_url: str, soup: BeautifulSoup) -> list[FrameFinding]:
    findings: list[FrameFinding] = []
    for tag in soup.find_all(["iframe", "frame"]):
        src = tag.get("src", "")
        findings.append(
            FrameFinding(
                tag=tag.name or "",
                src=urljoin(source_url, src) if src else "",
                id=attr_string(tag, "id"),
                name=attr_string(tag, "name"),
                classes=attr_string(tag, "class"),
            )
        )
    return findings


def extract_handlers(source_url: str, soup: BeautifulSoup) -> tuple[list[HandlerFinding], list[HandlerFinding]]:
    onclicks: list[HandlerFinding] = []
    javascript_hrefs: list[HandlerFinding] = []
    for tag in soup.find_all(True):
        href = tag.get("href")
        absolute_href = urljoin(source_url, href) if href and not href.startswith("javascript:") else href
        onclick = tag.get("onclick")
        finding = HandlerFinding(
            tag=tag.name or "",
            text=trim(tag.get_text(" ", strip=True), limit=120),
            href=absolute_href,
            onclick=str(onclick) if onclick else None,
        )
        if onclick:
            onclicks.append(finding)
        if isinstance(href, str) and href.lower().startswith("javascript:"):
            javascript_hrefs.append(finding)
    return onclicks, javascript_hrefs


def extract_keyword_findings(html: str) -> list[KeywordFinding]:
    findings: list[KeywordFinding] = []
    for keyword in KEYWORDS:
        count = html.count(keyword)
        snippets: list[str] = []
        search_from = 0
        while len(snippets) < 3:
            index = html.find(keyword, search_from)
            if index < 0:
                break
            snippets.append(trim(snippet_around(html, keyword)))
            search_from = index + len(keyword)
        findings.append(KeywordFinding(keyword=keyword, count=count, snippets=snippets))
    return findings


def extract_hidden_elements(soup: BeautifulSoup) -> list[HiddenFinding]:
    findings: list[HiddenFinding] = []
    for tag in soup.find_all(True):
        reasons: list[str] = []
        style = attr_string(tag, "style")
        if tag.has_attr("hidden"):
            reasons.append("hidden attribute")
        if HIDDEN_STYLE_RE.search(style):
            reasons.append(style)
        if attr_string(tag, "aria-hidden").lower() == "true":
            reasons.append("aria-hidden=true")
        if not reasons:
            continue
        findings.append(
            HiddenFinding(
                tag=tag.name or "",
                id=attr_string(tag, "id"),
                classes=attr_string(tag, "class"),
                reason="; ".join(reasons),
                text_snippet=trim(tag.get_text(" ", strip=True), limit=120),
            )
        )
    return findings


def extract_panel_candidates(soup: BeautifulSoup) -> list[PanelFinding]:
    findings: list[PanelFinding] = []
    for tag in soup.find_all(True):
        id_value = attr_string(tag, "id")
        classes = attr_string(tag, "class")
        combined = f"{id_value} {classes}"
        if not PANEL_RE.search(combined):
            continue
        findings.append(
            PanelFinding(
                tag=tag.name or "",
                id=id_value,
                classes=classes,
                text_snippet=trim(tag.get_text(" ", strip=True), limit=120),
            )
        )
    return findings


def nearby_urls_for_tag(source_url: str, tag: Tag) -> list[str]:
    source = str(tag)
    urls: list[str] = []
    for match in URL_FRAGMENT_RE.findall(source):
        if match.startswith("http"):
            urls.append(match)
        else:
            urls.append(urljoin(source_url, match))
    return list(dict.fromkeys(urls))


def looks_like_hymn_entry(text: str, href: str | None, onclick: str | None) -> bool:
    if "திருப்பூந்தராய்" in text:
        return True
    if len(text) <= 160 and "திரு" in text and ("-" in text or "உரை" in text):
        return True
    return False


def extract_hymn_candidates(source_url: str, soup: BeautifulSoup, limit: int = 10) -> list[HymnCandidate]:
    candidates: list[HymnCandidate] = []
    for tag in soup.find_all(["a", "button"]):
        text = trim(tag.get_text(" ", strip=True), limit=160)
        href = tag.get("href")
        onclick = tag.get("onclick")
        absolute_href = urljoin(source_url, href) if href and not href.startswith("javascript:") else href
        if not looks_like_hymn_entry(text, absolute_href, str(onclick) if onclick else None):
            continue
        candidates.append(
            HymnCandidate(
                text=text,
                href=absolute_href,
                onclick=str(onclick) if onclick else None,
                nearby_urls=nearby_urls_for_tag(source_url, tag),
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def discover_dynamic_content(source_url: str, html: str, source_path: str) -> DynamicDiscovery:
    soup = BeautifulSoup(html, "lxml")
    handlers, javascript_hrefs = extract_handlers(source_url, soup)
    return DynamicDiscovery(
        source_url=source_url,
        source_path=source_path,
        scripts=extract_scripts(source_url, soup),
        frames=extract_frames(source_url, soup),
        handlers=handlers,
        javascript_hrefs=javascript_hrefs,
        keywords=extract_keyword_findings(html),
        hidden_elements=extract_hidden_elements(soup),
        panels=extract_panel_candidates(soup),
        hymn_candidates=extract_hymn_candidates(source_url, soup),
    )


def render_markdown(discovery: DynamicDiscovery) -> str:
    lines = [
        "# Dynamic Content Discovery Report",
        "",
        f"- Source URL: `{discovery.source_url}`",
        f"- Source HTML: `{discovery.source_path}`",
        "",
        "## Summary",
        "",
        f"- Script tags: `{len(discovery.scripts)}`",
        f"- iframe/frame tags: `{len(discovery.frames)}`",
        f"- onclick handlers: `{len(discovery.handlers)}`",
        f"- javascript: hrefs: `{len(discovery.javascript_hrefs)}`",
        f"- hidden elements: `{len(discovery.hidden_elements)}`",
        f"- content-panel candidates: `{len(discovery.panels)}`",
        f"- first hymn/navigation candidates: `{len(discovery.hymn_candidates)}`",
        "",
        "## Tamil Keyword Evidence",
        "",
        "| Keyword | Count | Snippets |",
        "| --- | ---: | --- |",
    ]
    for finding in discovery.keywords:
        snippets = "<br/>".join(finding.snippets) if finding.snippets else ""
        lines.append(f"| {finding.keyword} | {finding.count} | {snippets} |")

    lines.extend(["", "## Frames", "", "| Tag | ID | Name | Class | Src |", "| --- | --- | --- | --- | --- |"])
    for frame in discovery.frames:
        lines.append(
            f"| `{frame.tag}` | `{frame.id}` | `{frame.name}` | `{frame.classes}` | `{frame.src}` |"
        )
    if not discovery.frames:
        lines.append("| | | | | |")

    lines.extend(["", "## Scripts", "", "| Src | Inline Chars | Snippet |", "| --- | ---: | --- |"])
    for script in discovery.scripts:
        lines.append(f"| `{script.src or ''}` | {script.inline_chars} | {script.snippet} |")

    lines.extend(["", "## onclick Handlers", "", "| Tag | Text | Href | onclick |", "| --- | --- | --- | --- |"])
    for handler in discovery.handlers:
        lines.append(
            f"| `{handler.tag}` | {handler.text} | `{handler.href or ''}` | `{trim(handler.onclick or '', 220)}` |"
        )
    if not discovery.handlers:
        lines.append("| | | | |")

    lines.extend(["", "## javascript: Hrefs", "", "| Tag | Text | Href |", "| --- | --- | --- |"])
    for handler in discovery.javascript_hrefs:
        lines.append(f"| `{handler.tag}` | {handler.text} | `{handler.href or ''}` |")
    if not discovery.javascript_hrefs:
        lines.append("| | | |")

    lines.extend(["", "## Hidden Elements", "", "| Tag | ID | Class | Reason | Text |", "| --- | --- | --- | --- | --- |"])
    for hidden in discovery.hidden_elements[:50]:
        lines.append(
            f"| `{hidden.tag}` | `{hidden.id}` | `{hidden.classes}` | {hidden.reason} | {hidden.text_snippet} |"
        )
    if not discovery.hidden_elements:
        lines.append("| | | | | |")

    lines.extend(
        ["", "## Content Panel Candidates", "", "| Tag | ID | Class | Text |", "| --- | --- | --- | --- |"]
    )
    for panel in discovery.panels[:80]:
        lines.append(f"| `{panel.tag}` | `{panel.id}` | `{panel.classes}` | {panel.text_snippet} |")
    if not discovery.panels:
        lines.append("| | | | |")

    lines.extend(
        [
            "",
            "## First 10 Hymn/Navigation Candidates",
            "",
            "| Text | Href | onclick | Nearby URLs |",
            "| --- | --- | --- | --- |",
        ]
    )
    for candidate in discovery.hymn_candidates:
        nearby = "<br/>".join(f"`{url}`" for url in candidate.nearby_urls)
        lines.append(
            f"| {candidate.text} | `{candidate.href or ''}` | `{trim(candidate.onclick or '', 180)}` | {nearby} |"
        )
    if not discovery.hymn_candidates:
        lines.append("| _No direct hymn entries found in wrapper HTML._ | | | |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If frames are present, inspect those frame URLs next before adding browser automation.",
            "- If Tamil keyword counts for hymn/commentary terms are zero in the wrapper, poem/commentary content is probably not embedded in the initial wrapper HTML.",
            "- If onclick or `javascript:` links contain deterministic URLs, those handlers may be parsed by a later pilot extractor.",
            "- If this static evidence is still insufficient, a later phase can introduce Playwright/Selenium for click behavior capture.",
            "",
        ]
    )
    return "\n".join(lines)


def print_hymn_helper(discovery: DynamicDiscovery) -> None:
    print("First 10 hymn/navigation candidates:")
    if not discovery.hymn_candidates:
        print("- No direct hymn candidates found in this HTML.")
        if discovery.frames:
            print("- Frame endpoints found; inspect these next:")
            for frame in discovery.frames:
                print(f"  - {frame.src}")
        return
    for index, candidate in enumerate(discovery.hymn_candidates, start=1):
        print(f"{index}. text={candidate.text!r}")
        print(f"   href={candidate.href!r}")
        print(f"   onclick={candidate.onclick!r}")
        for url in candidate.nearby_urls:
            print(f"   nearby_url={url}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover static evidence for TamilVU dynamic content")
    parser.add_argument("--url", default=TARGET_URL)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--fetch", action="store_true", help="Fetch the page again instead of only reading snapshot")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--print-hymn-neighborhood", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        html, source_path = load_html(
            url=args.url,
            snapshot_dir=args.snapshot_dir,
            fetch=args.fetch,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    discovery = discover_dynamic_content(args.url, html, str(source_path))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_markdown(discovery), encoding="utf-8")
    print(f"Report written to {args.report}")

    if args.print_hymn_neighborhood:
        print_hymn_helper(discovery)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
