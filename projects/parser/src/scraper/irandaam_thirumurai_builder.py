from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from tvu_common.snapshot import fetch_html, save_snapshot, snapshot_filename

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scraper.pilot_hymn_scraper import (
    CommentaryParts,
    PilotRecord,
    VerseCandidate,
    extract_query_params,
    is_internal_tamilvu_url,
    normalize_text,
    parse_hymn_page,
    split_commentary_text,
)

LEFT_FRAME_URL = "https://www.tamilvu.org/slet/l4120/l4120lft.jsp"
DEFAULT_OUTPUT_DIR = Path(".")
CORPUS_ROOT = Path("corpus/irandaam_thirumurai")
DEFAULT_JSONL_RELATIVE = Path("data/processed/corpus/irandaam_thirumurai.jsonl")
DEFAULT_HYMN_JSONL_DIR_RELATIVE = Path("data/processed/corpus/irandaam_thirumurai/hymns")
DEFAULT_REPORT_RELATIVE = Path("reports/irandaam-thirumurai-corpus-report.md")
DEFAULT_NAV_RAW_RELATIVE = Path("data/raw/corpus/irandaam_thirumurai/navigation")
DEFAULT_HYMN_RAW_RELATIVE = Path("data/raw/corpus/irandaam_thirumurai/hymns")
DEFAULT_COMMENTARY_RAW_RELATIVE = Path("data/raw/corpus/irandaam_thirumurai/commentary")


@dataclass(slots=True)
class HymnLink:
    hymn_id: str
    title: str
    url: str
    hymn_location: str
    hymn_note: str
    pann: str


@dataclass(slots=True)
class CorpusRecord:
    record_type: str
    source: str
    source_site: str
    language: str
    domain: str
    genre: str
    religious_tradition: str
    collection: str
    work: str
    thirumurai: str
    thirumurai_number: int
    author: str
    hymn_id: str
    hymn_title: str
    hymn_location: str
    hymn_note: str
    pann: str
    song_no: str
    verse_index_in_hymn: int
    verse_text: str
    commentary_available: bool
    pozhppurai: str
    kurippurai: str
    hymn_url: str
    commentary_url: str
    source_parameters: dict[str, str]
    text_statistics: dict[str, int]
    extraction_metadata: dict[str, object]


@dataclass(slots=True)
class HymnSummary:
    hymn_id: str
    title: str
    url: str
    attempted: bool
    success: bool
    record_count: int
    error: str


@dataclass(slots=True)
class CorpusValidation:
    ok: bool
    errors: list[str]
    warnings: list[str]
    total_hymn_links_discovered: int
    total_hymns_attempted: int
    total_hymns_successful: int
    total_verse_records_written: int
    missing_verse_text_count: int
    missing_commentary_url_count: int
    missing_pozhppurai_count: int
    missing_kurippurai_count: int
    duplicate_song_no: list[str]
    duplicate_source_urls: list[str]


def resolve_output_path(base_dir: Path, relative_path: Path) -> Path:
    return relative_path if relative_path.is_absolute() else base_dir / relative_path


def snapshot_path_for(url: str, output_dir: Path) -> Path:
    return output_dir / snapshot_filename(url)


def fetch_or_read_snapshot(url: str, output_dir: Path, timeout: int, resume: bool) -> str:
    path = snapshot_path_for(url, output_dir)
    if resume and path.exists():
        return path.read_text(encoding="utf-8")
    html = fetch_html(url, timeout=timeout)
    save_snapshot(url, html, output_dir)
    return html


def split_hymn_title(title: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in title.split(" - ") if part.strip()]
    if len(parts) >= 3:
        return parts[0], " - ".join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return title.strip(), "", ""


def extract_hymn_links(source_url: str, html: str) -> list[HymnLink]:
    soup = BeautifulSoup(html, "lxml")
    links: list[HymnLink] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        absolute_url = urljoin(source_url, href)
        params = extract_query_params(absolute_url)
        hymn_id = params.get("subid", "")
        if "l4120son.jsp" not in absolute_url or not hymn_id:
            continue
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        title = normalize_text(anchor.get_text(" ", strip=True))
        location, note, pann = split_hymn_title(title)
        links.append(
            HymnLink(
                hymn_id=hymn_id,
                title=title,
                url=absolute_url,
                hymn_location=location,
                hymn_note=note,
                pann=pann,
            )
        )
    return links


def text_statistics(verse_text: str, pozhppurai: str, kurippurai: str) -> dict[str, int]:
    tamil_chars = sum(1 for char in f"{verse_text}{pozhppurai}{kurippurai}" if "\u0B80" <= char <= "\u0BFF")
    return {
        "verse_chars": len(verse_text),
        "verse_lines": len([line for line in verse_text.splitlines() if line.strip()]),
        "pozhppurai_chars": len(pozhppurai),
        "kurippurai_chars": len(kurippurai),
        "tamil_chars": tamil_chars,
    }


def build_source_parameters(hymn: HymnLink, verse: VerseCandidate) -> dict[str, str]:
    params = {
        "subid": hymn.hymn_id,
        "sub_id": verse.sub_id or hymn.hymn_id,
        "song_no": verse.song_no,
        "book_id": verse.book_id,
        "head_id": verse.head_id,
    }
    return {key: value for key, value in params.items() if value}


def build_corpus_record(
    hymn: HymnLink,
    hymn_title: str,
    verse: VerseCandidate,
    verse_index: int,
    commentary: CommentaryParts,
    fetched_at: str,
) -> CorpusRecord:
    commentary_available = bool(verse.commentary_url)
    return CorpusRecord(
        record_type="verse_with_commentary",
        source="TamilVU",
        source_site="https://www.tamilvu.org",
        language="ta",
        domain="Tamil literature",
        genre="Devotional poetry",
        religious_tradition="Saivam",
        collection="Thevaram",
        work="Panniru Thirumurai",
        thirumurai="Irandaam Thirumurai",
        thirumurai_number=2,
        author="Sambandar",
        hymn_id=hymn.hymn_id,
        hymn_title=hymn_title or hymn.title,
        hymn_location=hymn.hymn_location,
        hymn_note=hymn.hymn_note,
        pann=hymn.pann,
        song_no=verse.song_no,
        verse_index_in_hymn=verse_index,
        verse_text=verse.verse_text,
        commentary_available=commentary_available,
        pozhppurai=commentary.pozhppurai,
        kurippurai=commentary.kurippurai,
        hymn_url=hymn.url,
        commentary_url=verse.commentary_url,
        source_parameters=build_source_parameters(hymn, verse),
        text_statistics=text_statistics(verse.verse_text, commentary.pozhppurai, commentary.kurippurai),
        extraction_metadata={
            "extractor": "irandaam_thirumurai_builder",
            "extractor_version": "0.1",
            "fetched_at": fetched_at,
            "extraction_status": commentary.extraction_status,
            "warnings": commentary.warnings,
        },
    )


def convert_to_pilot_record(record: CorpusRecord) -> PilotRecord:
    metadata = record.extraction_metadata
    return PilotRecord(
        record_type=record.record_type,
        source=record.source,
        work=record.work,
        collection=record.collection,
        thirumurai=record.thirumurai,
        author=record.author,
        hymn_title=record.hymn_title,
        sub_id=record.source_parameters.get("sub_id", record.hymn_id),
        book_id=record.source_parameters.get("book_id", ""),
        head_id=record.source_parameters.get("head_id", ""),
        song_no=record.song_no,
        verse_text=record.verse_text,
        pozhppurai=record.pozhppurai,
        kurippurai=record.kurippurai,
        hymn_url=record.hymn_url,
        commentary_url=record.commentary_url,
        language=record.language,
        extraction_status=str(metadata.get("extraction_status", "")),
    )


def scrape_hymn(
    hymn: HymnLink,
    delay: float,
    timeout: int,
    hymn_raw_dir: Path,
    commentary_raw_dir: Path,
    resume: bool,
) -> tuple[str, list[CorpusRecord]]:
    if not is_internal_tamilvu_url(hymn.url):
        raise ValueError(f"Refusing non-TamilVU hymn URL: {hymn.url}")

    hymn_html = fetch_or_read_snapshot(hymn.url, hymn_raw_dir, timeout=timeout, resume=resume)
    hymn_title, verses = parse_hymn_page(hymn.url, hymn_html)
    records: list[CorpusRecord] = []
    fetched_at = datetime.now(UTC).isoformat()

    for verse_index, verse in enumerate(verses, start=1):
        if not verse.commentary_url:
            commentary = CommentaryParts("", "", "missing_commentary_url", ["missing_commentary_url"])
        else:
            if delay > 0:
                time.sleep(delay)
            commentary_html = fetch_or_read_snapshot(
                verse.commentary_url,
                commentary_raw_dir,
                timeout=timeout,
                resume=resume,
            )
            commentary = split_commentary_text(commentary_html)
        records.append(build_corpus_record(hymn, hymn_title, verse, verse_index, commentary, fetched_at))
    return hymn_title, records


def write_jsonl(records: list[CorpusRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def validate_corpus(
    records: list[CorpusRecord],
    hymn_links_discovered: int,
    hymn_summaries: list[HymnSummary],
) -> CorpusValidation:
    errors: list[str] = []
    warnings: list[str] = []
    song_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    missing_verse_text = 0
    missing_commentary_url = 0
    missing_pozhppurai = 0
    missing_kurippurai = 0

    for record in records:
        if not record.verse_text:
            missing_verse_text += 1
        if not record.commentary_url:
            missing_commentary_url += 1
        if not record.pozhppurai:
            missing_pozhppurai += 1
        if not record.kurippurai:
            missing_kurippurai += 1
        if record.song_no:
            song_counts[record.song_no] = song_counts.get(record.song_no, 0) + 1
        if record.commentary_url:
            source_counts[record.commentary_url] = source_counts.get(record.commentary_url, 0) + 1

    duplicate_song_no = sorted(song_no for song_no, count in song_counts.items() if count > 1)
    duplicate_source_urls = sorted(url for url, count in source_counts.items() if count > 1)
    attempted = sum(1 for summary in hymn_summaries if summary.attempted)
    successful = sum(1 for summary in hymn_summaries if summary.success)

    if missing_verse_text:
        errors.append(f"missing verse text count: {missing_verse_text}")
    if duplicate_song_no:
        errors.append(f"duplicate song_no values: {', '.join(duplicate_song_no[:20])}")
    if duplicate_source_urls:
        errors.append(f"duplicate commentary URLs: {', '.join(duplicate_source_urls[:20])}")
    if missing_commentary_url:
        warnings.append(f"missing commentary URL count: {missing_commentary_url}")
    if missing_pozhppurai:
        warnings.append(f"missing pozhppurai count: {missing_pozhppurai}")
    if missing_kurippurai:
        warnings.append(f"missing kurippurai count: {missing_kurippurai}")

    return CorpusValidation(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        total_hymn_links_discovered=hymn_links_discovered,
        total_hymns_attempted=attempted,
        total_hymns_successful=successful,
        total_verse_records_written=len(records),
        missing_verse_text_count=missing_verse_text,
        missing_commentary_url_count=missing_commentary_url,
        missing_pozhppurai_count=missing_pozhppurai,
        missing_kurippurai_count=missing_kurippurai,
        duplicate_song_no=duplicate_song_no,
        duplicate_source_urls=duplicate_source_urls,
    )


def render_report(
    validation: CorpusValidation,
    hymn_summaries: list[HymnSummary],
    jsonl_path: Path,
    selected_count: int,
) -> str:
    lines = [
        "# Irandaam Thirumurai Corpus Report",
        "",
        f"- Navigation URL: `{LEFT_FRAME_URL}`",
        f"- JSONL output: `{jsonl_path}`",
        f"- Hymns selected this run: `{selected_count}`",
        f"- Total hymn links discovered: `{validation.total_hymn_links_discovered}`",
        f"- Total hymns attempted: `{validation.total_hymns_attempted}`",
        f"- Total hymns successful: `{validation.total_hymns_successful}`",
        f"- Total verse records written: `{validation.total_verse_records_written}`",
        f"- Validation OK: `{validation.ok}`",
        "",
        "## Validation Counts",
        "",
        f"- Missing verse text: `{validation.missing_verse_text_count}`",
        f"- Missing commentary URL: `{validation.missing_commentary_url_count}`",
        f"- Missing pozhppurai: `{validation.missing_pozhppurai_count}`",
        f"- Missing kurippurai: `{validation.missing_kurippurai_count}`",
        f"- Duplicate song_no values: `{len(validation.duplicate_song_no)}`",
        f"- Duplicate source URLs: `{len(validation.duplicate_source_urls)}`",
        "",
    ]
    if validation.errors:
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in validation.errors)
        lines.append("")
    if validation.warnings:
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in validation.warnings)
        lines.append("")
    if not validation.errors and not validation.warnings:
        lines.extend(["## Validation", "", "- No validation errors or warnings.", ""])

    lines.extend(
        [
            "## Per-Hymn Summary",
            "",
            "| Hymn ID | Status | Records | Title | URL |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for summary in hymn_summaries:
        status = "success" if summary.success else ("failed" if summary.attempted else "not_attempted")
        title = summary.title.replace("|", "\\|")
        error = f" ({summary.error})" if summary.error else ""
        lines.append(
            f"| `{summary.hymn_id}` | `{status}{error}` | {summary.record_count} | {title} | `{summary.url}` |"
        )
    return "\n".join(lines)


def build_corpus(
    left_frame_url: str,
    delay: float,
    limit: int | None,
    timeout: int,
    resume: bool,
    dry_run: bool,
    output_dir: Path,
) -> tuple[list[HymnLink], list[CorpusRecord], list[HymnSummary], CorpusValidation | None]:
    nav_raw_dir = resolve_output_path(output_dir, DEFAULT_NAV_RAW_RELATIVE)
    hymn_raw_dir = resolve_output_path(output_dir, DEFAULT_HYMN_RAW_RELATIVE)
    commentary_raw_dir = resolve_output_path(output_dir, DEFAULT_COMMENTARY_RAW_RELATIVE)

    left_html = fetch_or_read_snapshot(left_frame_url, nav_raw_dir, timeout=timeout, resume=resume)
    hymn_links = extract_hymn_links(left_frame_url, left_html)
    selected_links = hymn_links[:limit] if limit is not None else hymn_links

    if dry_run:
        return hymn_links, [], [
            HymnSummary(h.hymn_id, h.title, h.url, False, False, 0, "") for h in selected_links
        ], None

    all_records: list[CorpusRecord] = []
    summaries: list[HymnSummary] = []
    hymn_jsonl_dir = resolve_output_path(output_dir, DEFAULT_HYMN_JSONL_DIR_RELATIVE)

    for index, hymn in enumerate(selected_links, start=1):
        if index > 1 and delay > 0:
            time.sleep(delay)
        try:
            _hymn_title, records = scrape_hymn(
                hymn,
                delay=delay,
                timeout=timeout,
                hymn_raw_dir=hymn_raw_dir,
                commentary_raw_dir=commentary_raw_dir,
                resume=resume,
            )
            write_jsonl(records, hymn_jsonl_dir / f"hymn_{hymn.hymn_id}.jsonl")
            all_records.extend(records)
            summaries.append(HymnSummary(hymn.hymn_id, hymn.title, hymn.url, True, bool(records), len(records), ""))
        except Exception as exc:
            summaries.append(HymnSummary(hymn.hymn_id, hymn.title, hymn.url, True, False, 0, str(exc)))

    validation = validate_corpus(all_records, len(hymn_links), summaries)
    return hymn_links, all_records, summaries, validation


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a controlled Irandaam Thirumurai corpus")
    parser.add_argument("--left-frame-url", default=LEFT_FRAME_URL)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    jsonl_path = resolve_output_path(args.output_dir, DEFAULT_JSONL_RELATIVE)
    report_path = resolve_output_path(args.output_dir, DEFAULT_REPORT_RELATIVE)

    try:
        hymn_links, records, summaries, validation = build_corpus(
            left_frame_url=args.left_frame_url,
            delay=args.delay,
            limit=args.limit,
            timeout=args.timeout,
            resume=args.resume,
            dry_run=args.dry_run,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    selected = hymn_links[: args.limit] if args.limit is not None else hymn_links
    if args.dry_run:
        print(f"Discovered {len(hymn_links)} hymn links")
        for hymn in selected:
            print(f"{hymn.hymn_id}\t{hymn.title}\t{hymn.url}")
        return 0

    if validation is None:
        print("ERROR: validation missing", file=sys.stderr)
        return 1

    write_jsonl(records, jsonl_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(validation, summaries, jsonl_path, len(selected)), encoding="utf-8")

    print(f"Discovered {len(hymn_links)} hymn links")
    print(f"Wrote {len(records)} records to {jsonl_path}")
    print(f"Report written to {report_path}")
    if not validation.ok:
        for error in validation.errors:
            print(f"VALIDATION ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
