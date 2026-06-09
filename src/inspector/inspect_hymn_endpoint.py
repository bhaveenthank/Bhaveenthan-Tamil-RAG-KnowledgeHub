from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspector.site_inspector import USER_AGENT, fetch_html, save_snapshot

TARGET_URL = "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664"
DEFAULT_OUTPUT_DIR = Path("data/raw/inspection/hymns")
DEFAULT_REPORT_PATH = Path("reports/hymn-endpoint-inspection.md")
TAMILVU_HOST = "www.tamilvu.org"
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
KEYWORDS = ["திருப்பூந்தராய்", "உரை", "பொழிப்புரை", "குறிப்புரை", "இந்தளம்"]
URAI_RE = re.compile("உரை|பொழிப்புரை|குறிப்புரை")
HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.IGNORECASE)
VERSE_NUMBER_RE = re.compile(r"^\s*(?:[0-9]+|[௦-௯]+)[).:-]?\s*")


@dataclass(slots=True)
class LinkFinding:
    text: str
    href: str
    onclick: str | None
    tag: str


@dataclass(slots=True)
class TextBlock:
    tag: str
    text: str
    tamil_chars: int
    total_chars: int
    line_count: int
    id: str
    classes: str


@dataclass(slots=True)
class PoemBlock:
    tag: str
    text: str
    lines: list[str]
    line_count: int
    has_verse_number: bool
    tamil_chars: int


@dataclass(slots=True)
class TableRow:
    text: str
    cells: list[str]
    tamil_chars: int


@dataclass(slots=True)
class ScriptFinding:
    src: str | None
    inline_chars: int


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
class HiddenContent:
    tag: str
    id: str
    classes: str
    reason: str
    text: str


@dataclass(slots=True)
class KeywordFinding:
    keyword: str
    count: int
    snippets: list[str]


@dataclass(slots=True)
class HymnInspection:
    url: str
    snapshot_path: str
    title: str
    query_params: dict[str, list[str]]
    tamil_text_length: int
    text_blocks: list[TextBlock]
    poem_blocks: list[PoemBlock]
    table_rows: list[TableRow]
    links: list[LinkFinding]
    urai_links: list[LinkFinding]
    keywords: list[KeywordFinding]
    scripts: list[ScriptFinding]
    frames: list[FrameFinding]
    forms: list[FormFinding]
    hidden_content: list[HiddenContent]


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def trim(text: str, limit: int = 220) -> str:
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


def extract_query_params(url: str) -> dict[str, list[str]]:
    params: dict[str, list[str]] = {}
    for key, value in parse_qsl(urlparse(url).query, keep_blank_values=True):
        params.setdefault(key, []).append(value)
    return params


def snippet_around(text: str, keyword: str, radius: int = 80) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(keyword) + radius)
    return trim(text[start:end])


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


def text_lines(tag: Tag) -> list[str]:
    return [normalize_text(line) for line in tag.get_text("\n", strip=True).splitlines() if normalize_text(line)]


def extract_text_blocks(soup: BeautifulSoup, limit: int = 120) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for tag in soup.find_all(["p", "div", "td", "tr", "li", "blockquote", "pre"]):
        lines = text_lines(tag)
        text = trim("\n".join(lines), limit=320)
        if not text:
            continue
        tamil_chars = tamil_char_count(text)
        total_chars = len(text)
        if tamil_chars < 8:
            continue
        ratio = tamil_chars / max(total_chars, 1)
        if tamil_chars < 20 and ratio < 0.35:
            continue
        blocks.append(
            TextBlock(
                tag=tag.name or "",
                text=text,
                tamil_chars=tamil_chars,
                total_chars=total_chars,
                line_count=len(lines),
                id=attr_string(tag, "id"),
                classes=attr_string(tag, "class"),
            )
        )
        if len(blocks) >= limit:
            break
    return blocks


def looks_like_poem_block(lines: list[str], text: str) -> bool:
    tamil_chars = tamil_char_count(text)
    if tamil_chars < 20:
        return False
    if len(lines) >= 3:
        return True
    if VERSE_NUMBER_RE.search(text) and tamil_chars >= 12:
        return True
    return False


def extract_poem_blocks(soup: BeautifulSoup, limit: int = 80) -> list[PoemBlock]:
    blocks: list[PoemBlock] = []
    for tag in soup.find_all(["p", "td", "tr", "div", "pre"]):
        lines = text_lines(tag)
        text = "\n".join(lines)
        if not looks_like_poem_block(lines, text):
            continue
        blocks.append(
            PoemBlock(
                tag=tag.name or "",
                text=trim(text, limit=420),
                lines=lines[:12],
                line_count=len(lines),
                has_verse_number=bool(VERSE_NUMBER_RE.search(text)),
                tamil_chars=tamil_char_count(text),
            )
        )
        if len(blocks) >= limit:
            break
    return blocks


def extract_table_rows(soup: BeautifulSoup, limit: int = 120) -> list[TableRow]:
    rows: list[TableRow] = []
    for row in soup.find_all("tr"):
        cells = [trim(cell.get_text(" ", strip=True), limit=180) for cell in row.find_all(["td", "th"])]
        text = trim(row.get_text(" ", strip=True), limit=360)
        tamil_chars = tamil_char_count(text)
        if tamil_chars < 4:
            continue
        rows.append(TableRow(text=text, cells=[cell for cell in cells if cell], tamil_chars=tamil_chars))
        if len(rows) >= limit:
            break
    return rows


def extract_links(source_url: str, soup: BeautifulSoup) -> list[LinkFinding]:
    links: list[LinkFinding] = []
    for tag in soup.find_all(["a", "button", "input", "img"]):
        href = tag.get("href") or tag.get("src") or ""
        resolved = resolve_url(source_url, href)
        if resolved and not resolved.startswith("javascript:") and not is_internal_tamilvu_url(resolved):
            continue
        text_parts = [
            tag.get_text(" ", strip=True),
            attr_string(tag, "title"),
            attr_string(tag, "alt"),
            attr_string(tag, "value"),
            attr_string(tag, "aria-label"),
        ]
        text = trim(" ".join(part for part in text_parts if part), limit=180)
        links.append(
            LinkFinding(
                text=text,
                href=resolved,
                onclick=str(tag.get("onclick")) if tag.get("onclick") else None,
                tag=tag.name or "",
            )
        )
    return links


def extract_urai_links(links: list[LinkFinding]) -> list[LinkFinding]:
    return [
        link
        for link in links
        if URAI_RE.search(f"{link.text} {link.href} {link.onclick or ''}")
    ]


def extract_scripts(source_url: str, soup: BeautifulSoup) -> list[ScriptFinding]:
    scripts: list[ScriptFinding] = []
    for script in soup.find_all("script"):
        src = script.get("src")
        inline_text = script.string or script.get_text(" ", strip=True) or ""
        scripts.append(ScriptFinding(src=resolve_url(source_url, src) if src else None, inline_chars=len(inline_text)))
    return scripts


def extract_frames(source_url: str, soup: BeautifulSoup) -> list[FrameFinding]:
    frames: list[FrameFinding] = []
    for tag in soup.find_all(["iframe", "frame"]):
        frames.append(
            FrameFinding(
                tag=tag.name or "",
                src=resolve_url(source_url, tag.get("src", "")),
                id=attr_string(tag, "id"),
                name=attr_string(tag, "name"),
                classes=attr_string(tag, "class"),
            )
        )
    return frames


def extract_forms(source_url: str, soup: BeautifulSoup) -> list[FormFinding]:
    forms: list[FormFinding] = []
    for form in soup.find_all("form"):
        forms.append(
            FormFinding(
                method=attr_string(form, "method").lower() or "get",
                action=resolve_url(source_url, form.get("action", "")),
                id=attr_string(form, "id"),
                name=attr_string(form, "name"),
            )
        )
    return forms


def extract_hidden_content(soup: BeautifulSoup) -> list[HiddenContent]:
    hidden: list[HiddenContent] = []
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
        hidden.append(
            HiddenContent(
                tag=tag.name or "",
                id=attr_string(tag, "id"),
                classes=attr_string(tag, "class"),
                reason="; ".join(reasons),
                text=trim(tag.get_text(" ", strip=True), limit=180),
            )
        )
    return hidden


def inspect_html(url: str, html: str, snapshot_path: str) -> HymnInspection:
    soup = BeautifulSoup(html, "lxml")
    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    visible_text = soup.get_text("\n", strip=True)
    links = extract_links(url, soup)
    return HymnInspection(
        url=url,
        snapshot_path=snapshot_path,
        title=title,
        query_params=extract_query_params(url),
        tamil_text_length=tamil_char_count(visible_text),
        text_blocks=extract_text_blocks(soup),
        poem_blocks=extract_poem_blocks(soup),
        table_rows=extract_table_rows(soup),
        links=links,
        urai_links=extract_urai_links(links),
        keywords=extract_keywords(html),
        scripts=extract_scripts(url, soup),
        frames=extract_frames(url, soup),
        forms=extract_forms(url, soup),
        hidden_content=extract_hidden_content(soup),
    )


def markdown_cell(value: str | None) -> str:
    return (value or "").replace("|", "\\|").replace("\n", "<br/>")


def render_report(inspection: HymnInspection) -> str:
    lines = [
        "# Hymn Endpoint Inspection Report",
        "",
        "This report inspects exactly one selected hymn endpoint and does not recursively crawl.",
        "",
        f"- URL: `{inspection.url}`",
        f"- Snapshot: `{inspection.snapshot_path}`",
        f"- Page title: `{inspection.title}`",
        f"- Rough Tamil text length: `{inspection.tamil_text_length}`",
        f"- Visible Tamil-heavy text blocks: `{len(inspection.text_blocks)}`",
        f"- Possible poem/verse blocks: `{len(inspection.poem_blocks)}`",
        f"- Table rows with Tamil text: `{len(inspection.table_rows)}`",
        f"- Links/buttons/icons: `{len(inspection.links)}`",
        f"- Possible உரை links/buttons/icons: `{len(inspection.urai_links)}`",
        f"- Scripts: `{len(inspection.scripts)}`",
        f"- Frames/iframes: `{len(inspection.frames)}`",
        f"- Forms: `{len(inspection.forms)}`",
        f"- Hidden content elements: `{len(inspection.hidden_content)}`",
        "",
        "## URL Parameters",
        "",
        "| Parameter | Values |",
        "| --- | --- |",
    ]
    for key, values in inspection.query_params.items():
        lines.append(f"| `{markdown_cell(key)}` | `{markdown_cell(', '.join(values))}` |")
    if not inspection.query_params:
        lines.append("| _None._ | |")

    lines.extend(["", "## Tamil Keyword Matches", "", "| Keyword | Count | Snippets |", "| --- | ---: | --- |"])
    for keyword in inspection.keywords:
        snippets = "<br/>".join(markdown_cell(snippet) for snippet in keyword.snippets)
        lines.append(f"| {keyword.keyword} | {keyword.count} | {snippets} |")

    lines.extend(
        [
            "",
            "## Possible Poem/Verse Blocks",
            "",
            "| Tag | Lines | Verse Number? | Tamil Chars | Text |",
            "| --- | ---: | --- | ---: | --- |",
        ]
    )
    for block in inspection.poem_blocks:
        lines.append(
            f"| `{block.tag}` | {block.line_count} | `{block.has_verse_number}` | {block.tamil_chars} | {markdown_cell(block.text)} |"
        )
    if not inspection.poem_blocks:
        lines.append("| _None detected by heuristic._ | | | | |")

    lines.extend(
        [
            "",
            "## Visible Tamil-Heavy Text Blocks",
            "",
            "| Tag | Lines | Tamil Chars | ID | Class | Text |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for block in inspection.text_blocks[:100]:
        lines.append(
            f"| `{block.tag}` | {block.line_count} | {block.tamil_chars} | `{markdown_cell(block.id)}` | `{markdown_cell(block.classes)}` | {markdown_cell(block.text)} |"
        )

    lines.extend(["", "## Table Rows", "", "| Tamil Chars | Cells | Text |", "| ---: | --- | --- |"])
    for row in inspection.table_rows[:100]:
        cells = "<br/>".join(markdown_cell(cell) for cell in row.cells)
        lines.append(f"| {row.tamil_chars} | {cells} | {markdown_cell(row.text)} |")
    if not inspection.table_rows:
        lines.append("| | _None._ | |")

    lines.extend(["", "## Links / Buttons / Icons", "", "| Tag | Text | Href/Src | onclick |", "| --- | --- | --- | --- |"])
    for link in inspection.links:
        lines.append(
            f"| `{link.tag}` | {markdown_cell(link.text)} | `{markdown_cell(link.href)}` | `{markdown_cell(link.onclick)}` |"
        )
    if not inspection.links:
        lines.append("| _None._ | | | |")

    lines.extend(["", "## Possible உரை Controls", "", "| Tag | Text | Href/Src | onclick |", "| --- | --- | --- | --- |"])
    for link in inspection.urai_links:
        lines.append(
            f"| `{link.tag}` | {markdown_cell(link.text)} | `{markdown_cell(link.href)}` | `{markdown_cell(link.onclick)}` |"
        )
    if not inspection.urai_links:
        lines.append("| _None detected._ | | | |")

    lines.extend(["", "## Scripts", "", "| Src | Inline Chars |", "| --- | ---: |"])
    for script in inspection.scripts:
        lines.append(f"| `{markdown_cell(script.src)}` | {script.inline_chars} |")
    if not inspection.scripts:
        lines.append("| _None._ | |")

    lines.extend(["", "## Frames / iframes", "", "| Tag | ID | Name | Class | Src |", "| --- | --- | --- | --- | --- |"])
    for frame in inspection.frames:
        lines.append(
            f"| `{frame.tag}` | `{markdown_cell(frame.id)}` | `{markdown_cell(frame.name)}` | `{markdown_cell(frame.classes)}` | `{markdown_cell(frame.src)}` |"
        )
    if not inspection.frames:
        lines.append("| _None._ | | | | |")

    lines.extend(["", "## Forms", "", "| Method | Action | ID | Name |", "| --- | --- | --- | --- |"])
    for form in inspection.forms:
        lines.append(
            f"| `{form.method}` | `{markdown_cell(form.action)}` | `{markdown_cell(form.id)}` | `{markdown_cell(form.name)}` |"
        )
    if not inspection.forms:
        lines.append("| _None._ | | | |")

    lines.extend(["", "## Hidden Content", "", "| Tag | ID | Class | Reason | Text |", "| --- | --- | --- | --- | --- |"])
    for hidden in inspection.hidden_content:
        lines.append(
            f"| `{hidden.tag}` | `{markdown_cell(hidden.id)}` | `{markdown_cell(hidden.classes)}` | {markdown_cell(hidden.reason)} | {markdown_cell(hidden.text)} |"
        )
    if not inspection.hidden_content:
        lines.append("| _None detected._ | | | | |")

    return "\n".join(lines)


def print_text_blocks(inspection: HymnInspection) -> None:
    print("Visible Tamil-heavy text blocks:")
    for index, block in enumerate(inspection.text_blocks, start=1):
        print(f"{index}. tag={block.tag} lines={block.line_count} tamil={block.tamil_chars}")
        print(block.text)


def print_links(inspection: HymnInspection) -> None:
    print("Links/buttons/icons:")
    for link in inspection.links:
        print(f"- tag={link.tag!r} text={link.text!r} href={link.href!r} onclick={link.onclick!r}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect one TamilVU hymn endpoint")
    parser.add_argument("--url", default=TARGET_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--print-text-blocks", action="store_true")
    parser.add_argument("--print-links", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not is_internal_tamilvu_url(args.url):
        print(f"ERROR: refusing non-TamilVU URL: {args.url}", file=sys.stderr)
        return 1

    html = fetch_html(args.url, timeout=args.timeout)
    snapshot_path = save_snapshot(args.url, html, args.output_dir)
    inspection = inspect_html(args.url, html, str(snapshot_path))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(inspection), encoding="utf-8")
    print(f"Report written to {args.report}")

    if args.print_text_blocks:
        print_text_blocks(inspection)
    if args.print_links:
        print_links(inspection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

