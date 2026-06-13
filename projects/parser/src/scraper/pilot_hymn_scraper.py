from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from tvu_common.snapshot import fetch_html, save_snapshot

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_HYMN_URL = "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664"
DEFAULT_HYMN_RAW_DIR = Path("data/raw/pilot/hymns")
DEFAULT_COMMENTARY_RAW_DIR = Path("data/raw/pilot/commentary")
DEFAULT_JSONL_PATH = Path("data/processed/pilot/thevaram_hymn_1664.jsonl")
DEFAULT_REPORT_PATH = Path("reports/pilot-hymn-1664-report.md")
EXPECTED_COMMENTARY_COUNT = 10
TAMILVU_HOST = "www.tamilvu.org"

COMMENTARY_URL_RE = re.compile(r"window\.open\('([^']+)'")
COMMENTARY_LABEL_RE = re.compile(r"(?:\d+\.\s*)?(?:பொழிப்புரை|பொ-ரை)\s*[:;]")
KURIPPURAI_LABEL_RE = re.compile(r"(?:குறிப்புரை|கு-ரை)\s*[:;]")


@dataclass(slots=True)
class VerseCandidate:
    song_no: str
    verse_number: str
    verse_text: str
    commentary_url: str
    book_id: str
    head_id: str
    sub_id: str


@dataclass(slots=True)
class CommentaryParts:
    pozhppurai: str
    kurippurai: str
    extraction_status: str
    warnings: list[str]


@dataclass(slots=True)
class PilotRecord:
    record_type: str
    source: str
    work: str
    collection: str
    thirumurai: str
    author: str
    hymn_title: str
    sub_id: str
    book_id: str
    head_id: str
    song_no: str
    verse_text: str
    pozhppurai: str
    kurippurai: str
    hymn_url: str
    commentary_url: str
    language: str
    extraction_status: str


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


def text_lines(tag: Tag) -> list[str]:
    return [normalize_text(line) for line in tag.get_text("\n", strip=True).splitlines() if normalize_text(line)]


def is_internal_tamilvu_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in {"", TAMILVU_HOST}


def extract_query_params(url: str) -> dict[str, str]:
    return {key: value for key, value in parse_qsl(urlparse(url).query, keep_blank_values=True)}


def extract_hymn_title(soup: BeautifulSoup) -> str:
    subhead = soup.find(class_="subhead")
    if subhead:
        title = normalize_text(subhead.get_text(" ", strip=True))
        if title:
            return title
    for bold in soup.find_all("b"):
        title = normalize_text(bold.get_text(" ", strip=True))
        if "திருப்பூந்தராய்" in title or "இந்தளம்" in title:
            return title
    return ""


def extract_commentary_url(source_url: str, outer_row: Tag) -> str:
    link = outer_row.find("a", string=lambda value: value and "உரை" in value)
    if not link:
        link = outer_row.find("a", onclick=True)
    if not link:
        return ""
    onclick = link.get("onclick", "")
    match = COMMENTARY_URL_RE.search(onclick)
    if not match:
        return ""
    return urljoin(source_url, match.group(1))


def parse_verse_from_poem_cell(source_url: str, poem_cell: Tag) -> VerseCandidate | None:
    inner_row = poem_cell.find("tr")
    if not inner_row:
        return None
    cells = inner_row.find_all("td", recursive=False)
    if len(cells) < 2:
        return None

    visible_song_no = normalize_text(cells[0].get_text(" ", strip=True)).rstrip(".")
    verse_number = normalize_text(cells[-1].get_text(" ", strip=True))
    verse_lines = text_lines(cells[1])
    verse_text = "\n".join(verse_lines)
    outer_row = poem_cell.find_parent("tr")
    commentary_url = extract_commentary_url(source_url, outer_row) if outer_row else ""
    params = extract_query_params(commentary_url)
    song_no = params.get("song_no", visible_song_no)

    if not song_no or not verse_text:
        return None

    return VerseCandidate(
        song_no=song_no,
        verse_number=verse_number,
        verse_text=verse_text,
        commentary_url=commentary_url,
        book_id=params.get("book_id", ""),
        head_id=params.get("head_id", ""),
        sub_id=params.get("sub_id", params.get("subid", "")),
    )


def parse_hymn_page(source_url: str, html: str) -> tuple[str, list[VerseCandidate]]:
    soup = BeautifulSoup(html, "lxml")
    hymn_title = extract_hymn_title(soup)
    verses: list[VerseCandidate] = []
    for poem_cell in soup.find_all("td", class_="poem"):
        verse = parse_verse_from_poem_cell(source_url, poem_cell)
        if verse:
            verses.append(verse)
    return hymn_title, verses


def split_commentary_text(html: str) -> CommentaryParts:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = normalize_text(text)

    warnings: list[str] = []
    pozh_match = COMMENTARY_LABEL_RE.search(text)
    kuri_match = KURIPPURAI_LABEL_RE.search(text)

    if not pozh_match:
        warnings.append("missing_pozhppurai")
    if not kuri_match:
        warnings.append("missing_kurippurai")

    pozhppurai = ""
    kurippurai = ""
    if pozh_match:
        pozh_start = pozh_match.end()
        pozh_end = kuri_match.start() if kuri_match else len(text)
        pozhppurai = normalize_text(text[pozh_start:pozh_end])
    if kuri_match:
        kurippurai = normalize_text(text[kuri_match.end():])

    status = "success" if pozhppurai and kurippurai else "partial_commentary"
    return CommentaryParts(
        pozhppurai=pozhppurai,
        kurippurai=kurippurai,
        extraction_status=status,
        warnings=warnings,
    )


def build_record(
    hymn_url: str,
    hymn_title: str,
    verse: VerseCandidate,
    commentary: CommentaryParts,
) -> PilotRecord:
    return PilotRecord(
        record_type="verse_with_commentary",
        source="TamilVU",
        work="Panniru Thirumurai",
        collection="Thevaram",
        thirumurai="Irandaam Thirumurai",
        author="Sambandar",
        hymn_title=hymn_title,
        sub_id=verse.sub_id,
        book_id=verse.book_id,
        head_id=verse.head_id,
        song_no=verse.song_no,
        verse_text=verse.verse_text,
        pozhppurai=commentary.pozhppurai,
        kurippurai=commentary.kurippurai,
        hymn_url=hymn_url,
        commentary_url=verse.commentary_url,
        language="ta",
        extraction_status=commentary.extraction_status,
    )


def validate_records(records: list[PilotRecord], commentary_url_count: int) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if commentary_url_count != EXPECTED_COMMENTARY_COUNT:
        errors.append(
            f"expected {EXPECTED_COMMENTARY_COUNT} commentary URLs, found {commentary_url_count}"
        )
    if len(records) < EXPECTED_COMMENTARY_COUNT:
        errors.append(f"expected at least {EXPECTED_COMMENTARY_COUNT} verse records, found {len(records)}")

    for index, record in enumerate(records, start=1):
        if not record.song_no:
            errors.append(f"record {index} missing song_no")
        if not record.verse_text:
            errors.append(f"record {index} missing verse_text")
        if not record.commentary_url:
            errors.append(f"record {index} missing commentary_url")
        missing_commentary = not record.pozhppurai or not record.kurippurai
        if missing_commentary and record.extraction_status == "success":
            errors.append(f"record {index} has success status but missing commentary text")
        if missing_commentary:
            warnings.append(f"record {index} has partial commentary extraction")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def write_jsonl(records: list[PilotRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def render_report(
    records: list[PilotRecord],
    validation: ValidationResult,
    hymn_title: str,
    hymn_url: str,
    jsonl_path: Path,
) -> str:
    success_count = sum(1 for record in records if record.extraction_status == "success")
    lines = [
        "# Pilot Hymn 1664 Report",
        "",
        f"- Hymn URL: `{hymn_url}`",
        f"- Hymn title: `{hymn_title}`",
        f"- JSONL output: `{jsonl_path}`",
        f"- Records: `{len(records)}`",
        f"- Successful records: `{success_count}`",
        f"- Validation OK: `{validation.ok}`",
        "",
        "## Validation",
        "",
    ]
    if validation.errors:
        lines.append("### Errors")
        lines.extend(f"- {error}" for error in validation.errors)
        lines.append("")
    if validation.warnings:
        lines.append("### Warnings")
        lines.extend(f"- {warning}" for warning in validation.warnings)
        lines.append("")
    if not validation.errors and not validation.warnings:
        lines.append("- No validation errors or warnings.")
        lines.append("")

    lines.extend(
        [
            "## Records",
            "",
            "| Song No | Status | Verse Preview | Commentary URL |",
            "| --- | --- | --- | --- |",
        ]
    )
    for record in records:
        preview = normalize_text(record.verse_text)[:120].replace("|", "\\|")
        lines.append(
            f"| `{record.song_no}` | `{record.extraction_status}` | {preview} | `{record.commentary_url}` |"
        )
    return "\n".join(lines)


def scrape_pilot_hymn(
    hymn_url: str,
    delay: float,
    timeout: int,
    hymn_raw_dir: Path,
    commentary_raw_dir: Path,
) -> tuple[str, list[PilotRecord]]:
    if not is_internal_tamilvu_url(hymn_url):
        raise ValueError(f"Refusing non-TamilVU hymn URL: {hymn_url}")

    hymn_html = fetch_html(hymn_url, timeout=timeout)
    save_snapshot(hymn_url, hymn_html, hymn_raw_dir)
    hymn_title, verses = parse_hymn_page(hymn_url, hymn_html)

    records: list[PilotRecord] = []
    for index, verse in enumerate(verses):
        if not verse.commentary_url:
            commentary = CommentaryParts("", "", "missing_commentary_url", ["missing_commentary_url"])
        else:
            if index > 0 or delay > 0:
                time.sleep(delay)
            commentary_html = fetch_html(verse.commentary_url, timeout=timeout)
            save_snapshot(verse.commentary_url, commentary_html, commentary_raw_dir)
            commentary = split_commentary_text(commentary_html)
        records.append(build_record(hymn_url, hymn_title, verse, commentary))

    return hymn_title, records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape exactly one TamilVU Thevaram hymn pilot")
    parser.add_argument("--hymn-url", default=DEFAULT_HYMN_URL)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--hymn-raw-dir", type=Path, default=DEFAULT_HYMN_RAW_DIR)
    parser.add_argument("--commentary-raw-dir", type=Path, default=DEFAULT_COMMENTARY_RAW_DIR)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        hymn_title, records = scrape_pilot_hymn(
            hymn_url=args.hymn_url,
            delay=args.delay,
            timeout=args.timeout,
            hymn_raw_dir=args.hymn_raw_dir,
            commentary_raw_dir=args.commentary_raw_dir,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    validation = validate_records(records, commentary_url_count=len({r.commentary_url for r in records if r.commentary_url}))
    write_jsonl(records, args.jsonl)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_report(records, validation, hymn_title, args.hymn_url, args.jsonl),
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} records to {args.jsonl}")
    print(f"Report written to {args.report}")
    if not validation.ok:
        for error in validation.errors:
            print(f"VALIDATION ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
