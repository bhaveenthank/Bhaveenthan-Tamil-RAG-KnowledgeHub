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

from inspector.site_inspector import fetch_html, save_snapshot

TARGET_URL = "https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664"
DEFAULT_OUTPUT_DIR = Path("data/raw/inspection/commentary")
DEFAULT_REPORT_PATH = Path("reports/commentary-endpoint-inspection.md")
TAMILVU_HOST = "www.tamilvu.org"
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
LABELS = ["பாடல்", "பொழிப்புரை", "குறிப்புரை", "உரை"]
HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.IGNORECASE)


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
class HeadingFinding:
    tag: str
    text: str


@dataclass(slots=True)
class LabelFinding:
    label: str
    count: int
    snippets: list[str]


@dataclass(slots=True)
class LinkFinding:
    tag: str
    text: str
    href: str
    onclick: str | None


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
class CommentaryInspection:
    url: str
    snapshot_path: str
    title: str
    query_params: dict[str, list[str]]
    tamil_text_length: int
    text_blocks: list[TextBlock]
    headings: list[HeadingFinding]
    labels: list[LabelFinding]
    links: list[LinkFinding]
    scripts: list[ScriptFinding]
    frames: list[FrameFinding]
    forms: list[FormFinding]
    hidden_content: list[HiddenContent]
    extractable_static: bool
    extractability_notes: list[str]


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def trim(text: str, limit: int = 260) -> str:
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


def text_lines(tag: Tag) -> list[str]:
    return [normalize_text(line) for line in tag.get_text("\n", strip=True).splitlines() if normalize_text(line)]


def extract_text_blocks(soup: BeautifulSoup, limit: int = 120) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for tag in soup.find_all(["p", "div", "td", "tr", "li", "blockquote", "pre"]):
        lines = text_lines(tag)
        text = trim("\n".join(lines), limit=420)
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


def extract_headings(soup: BeautifulSoup) -> list[HeadingFinding]:
    headings: list[HeadingFinding] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "b", "strong", "th"]):
        text = trim(tag.get_text(" ", strip=True), limit=180)
        if not text or tamil_char_count(text) < 2:
            continue
        headings.append(HeadingFinding(tag=tag.name or "", text=text))
    return headings


def snippet_around(text: str, label: str, radius: int = 80) -> str:
    index = text.find(label)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(label) + radius)
    return trim(text[start:end])


def extract_labels(html: str) -> list[LabelFinding]:
    findings: list[LabelFinding] = []
    for label in LABELS:
        count = html.count(label)
        snippets: list[str] = []
        start = 0
        while len(snippets) < 3:
            index = html.find(label, start)
            if index < 0:
                break
            snippets.append(snippet_around(html[index:], label))
            start = index + len(label)
        findings.append(LabelFinding(label=label, count=count, snippets=snippets))
    return findings


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
        links.append(
            LinkFinding(
                tag=tag.name or "",
                text=trim(" ".join(part for part in text_parts if part), limit=180),
                href=resolved,
                onclick=str(tag.get("onclick")) if tag.get("onclick") else None,
            )
        )
    return links


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
                text=trim(tag.get_text(" ", strip=True), limit=200),
            )
        )
    return hidden


def judge_static_extractability(
    text_blocks: list[TextBlock],
    labels: list[LabelFinding],
    frames: list[FrameFinding],
    forms: list[FormFinding],
    hidden_content: list[HiddenContent],
) -> tuple[bool, list[str]]:
    notes: list[str] = []
    label_counts = {label.label: label.count for label in labels}
    has_commentary_label = label_counts.get("பொழிப்புரை", 0) > 0 or label_counts.get("குறிப்புரை", 0) > 0
    has_text = bool(text_blocks)
    if has_text:
        notes.append("Visible Tamil text blocks are present in fetched HTML.")
    else:
        notes.append("No substantial visible Tamil text blocks were detected.")
    if has_commentary_label:
        notes.append("Commentary labels are present in fetched HTML.")
    else:
        notes.append("Commentary labels were not detected in fetched HTML.")
    if frames:
        notes.append("Frames/iframes are present; extraction may need nested endpoint inspection.")
    if forms:
        notes.append("Forms are present; verify they are not required for revealing content.")
    if hidden_content:
        notes.append("Hidden content elements are present; parser may need hidden DOM handling.")
    extractable = has_text and has_commentary_label and not frames
    return extractable, notes


def inspect_html(url: str, html: str, snapshot_path: str) -> CommentaryInspection:
    soup = BeautifulSoup(html, "lxml")
    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    visible_text = soup.get_text("\n", strip=True)
    text_blocks = extract_text_blocks(soup)
    labels = extract_labels(html)
    frames = extract_frames(url, soup)
    forms = extract_forms(url, soup)
    hidden_content = extract_hidden_content(soup)
    extractable_static, extractability_notes = judge_static_extractability(
        text_blocks=text_blocks,
        labels=labels,
        frames=frames,
        forms=forms,
        hidden_content=hidden_content,
    )
    return CommentaryInspection(
        url=url,
        snapshot_path=snapshot_path,
        title=title,
        query_params=extract_query_params(url),
        tamil_text_length=tamil_char_count(visible_text),
        text_blocks=text_blocks,
        headings=extract_headings(soup),
        labels=labels,
        links=extract_links(url, soup),
        scripts=extract_scripts(url, soup),
        frames=frames,
        forms=forms,
        hidden_content=hidden_content,
        extractable_static=extractable_static,
        extractability_notes=extractability_notes,
    )


def markdown_cell(value: str | None) -> str:
    return (value or "").replace("|", "\\|").replace("\n", "<br/>")


def render_report(inspection: CommentaryInspection) -> str:
    lines = [
        "# Commentary Endpoint Inspection Report",
        "",
        "This report inspects exactly one commentary endpoint and does not recursively crawl.",
        "",
        f"- URL: `{inspection.url}`",
        f"- Snapshot: `{inspection.snapshot_path}`",
        f"- Page title: `{inspection.title}`",
        f"- Rough Tamil text length: `{inspection.tamil_text_length}`",
        f"- Visible Tamil-heavy text blocks: `{len(inspection.text_blocks)}`",
        f"- Detected headings: `{len(inspection.headings)}`",
        f"- Links/buttons/icons: `{len(inspection.links)}`",
        f"- Scripts: `{len(inspection.scripts)}`",
        f"- Frames/iframes: `{len(inspection.frames)}`",
        f"- Forms: `{len(inspection.forms)}`",
        f"- Hidden content elements: `{len(inspection.hidden_content)}`",
        f"- Appears extractable with requests + BeautifulSoup: `{inspection.extractable_static}`",
        "",
        "## Extractability Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in inspection.extractability_notes)

    lines.extend(["", "## URL Parameters", "", "| Parameter | Values |", "| --- | --- |"])
    for key, values in inspection.query_params.items():
        lines.append(f"| `{markdown_cell(key)}` | `{markdown_cell(', '.join(values))}` |")
    if not inspection.query_params:
        lines.append("| _None._ | |")

    lines.extend(["", "## Detected Labels", "", "| Label | Count | Snippets |", "| --- | ---: | --- |"])
    for label in inspection.labels:
        snippets = "<br/>".join(markdown_cell(snippet) for snippet in label.snippets)
        lines.append(f"| {label.label} | {label.count} | {snippets} |")

    lines.extend(["", "## Headings", "", "| Tag | Text |", "| --- | --- |"])
    for heading in inspection.headings:
        lines.append(f"| `{heading.tag}` | {markdown_cell(heading.text)} |")
    if not inspection.headings:
        lines.append("| _None._ | |")

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
    if not inspection.text_blocks:
        lines.append("| _None._ | | | | | |")

    lines.extend(["", "## Links / Buttons / Icons", "", "| Tag | Text | Href/Src | onclick |", "| --- | --- | --- | --- |"])
    for link in inspection.links:
        lines.append(
            f"| `{link.tag}` | {markdown_cell(link.text)} | `{markdown_cell(link.href)}` | `{markdown_cell(link.onclick)}` |"
        )
    if not inspection.links:
        lines.append("| _None._ | | | |")

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


def print_text_blocks(inspection: CommentaryInspection) -> None:
    print("Visible Tamil-heavy text blocks:")
    for index, block in enumerate(inspection.text_blocks, start=1):
        print(f"{index}. tag={block.tag} lines={block.line_count} tamil={block.tamil_chars}")
        print(block.text)


def print_links(inspection: CommentaryInspection) -> None:
    print("Links/buttons/icons:")
    for link in inspection.links:
        print(f"- tag={link.tag!r} text={link.text!r} href={link.href!r} onclick={link.onclick!r}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect one TamilVU commentary endpoint")
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

