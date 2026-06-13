from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scraper.irandaam_thirumurai_builder import (
    LEFT_FRAME_URL,
    CorpusRecord,
    HymnLink,
    extract_hymn_links,
    fetch_or_read_snapshot,
    resolve_output_path,
    scrape_hymn,
    snapshot_path_for,
)

DEFAULT_OUTPUT_DIR = Path(".")
DEFAULT_REPORT_RELATIVE = Path("reports/corpus-validation-sampling-report.md")
DEFAULT_VALIDATION_RAW_ROOT = Path("data/raw/validation/corpus_sampling")
DEFAULT_NAV_RAW_RELATIVE = DEFAULT_VALIDATION_RAW_ROOT / "navigation"
DEFAULT_HYMN_RAW_RELATIVE = DEFAULT_VALIDATION_RAW_ROOT / "hymns"
DEFAULT_COMMENTARY_RAW_RELATIVE = DEFAULT_VALIDATION_RAW_ROOT / "commentary"
DEFAULT_SAMPLE_GROUP_SIZE = 5
UNUSUAL_VERSE_MIN = 8
UNUSUAL_VERSE_MAX = 12


@dataclass(slots=True)
class SampleResult:
    hymn_id: str
    hymn_title: str
    hymn_url: str
    sample_group: str
    verse_count: int
    commentary_count: int
    missing_verse_text: int
    missing_pozhppurai: int
    missing_kurippurai: int
    success: bool
    anomalies: list[str]
    error: str


@dataclass(slots=True)
class SampleSummary:
    sampled_hymns: int
    successful_hymns: int
    failed_hymns: int
    average_verses_per_hymn: float
    average_commentary_coverage: float


def select_sample_hymns(hymn_links: list[HymnLink], group_size: int = DEFAULT_SAMPLE_GROUP_SIZE) -> list[tuple[str, HymnLink]]:
    if not hymn_links:
        return []

    sample: list[tuple[str, HymnLink]] = []
    seen: set[str] = set()

    def add_group(group: str, links: list[HymnLink]) -> None:
        for hymn in links:
            if hymn.url in seen:
                continue
            seen.add(hymn.url)
            sample.append((group, hymn))

    middle_start = max(0, (len(hymn_links) // 2) - (group_size // 2))
    add_group("first", hymn_links[:group_size])
    add_group("middle", hymn_links[middle_start : middle_start + group_size])
    add_group("last", hymn_links[-group_size:])
    return sample


def has_unexpected_hymn_url(url: str) -> bool:
    return "l4120son.jsp?subid=" not in url


def has_unexpected_commentary_url(url: str) -> bool:
    return bool(url) and "l4120uri.jsp?" not in url


def detect_record_anomalies(records: list[CorpusRecord], hymn_html: str) -> list[str]:
    anomalies: list[str] = []
    song_counts: dict[str, int] = {}

    if 'class="poem"' not in hymn_html and "class=poem" not in hymn_html:
        anomalies.append("different_html_structure:no_poem_class_marker")
    if not records:
        anomalies.append("different_html_structure:no_verse_records")

    for record in records:
        if record.song_no:
            song_counts[record.song_no] = song_counts.get(record.song_no, 0) + 1
        if has_unexpected_hymn_url(record.hymn_url):
            anomalies.append(f"unexpected_hymn_url:{record.hymn_url}")
        if has_unexpected_commentary_url(record.commentary_url):
            anomalies.append(f"unexpected_commentary_url:{record.commentary_url}")
        if record.commentary_available and (not record.pozhppurai or not record.kurippurai):
            warnings = record.extraction_metadata.get("warnings", [])
            if warnings:
                anomalies.append("different_commentary_labels:" + ",".join(str(item) for item in warnings))

    duplicates = sorted(song_no for song_no, count in song_counts.items() if count > 1)
    for song_no in duplicates:
        anomalies.append(f"duplicate_song_no:{song_no}")

    if records and not (UNUSUAL_VERSE_MIN <= len(records) <= UNUSUAL_VERSE_MAX):
        anomalies.append(f"unusual_verse_count:{len(records)}")

    missing_commentary = sum(1 for record in records if not record.commentary_url)
    if missing_commentary:
        anomalies.append(f"missing_commentary_links:{missing_commentary}")

    return sorted(set(anomalies))


def summarize_records(
    hymn: HymnLink,
    group: str,
    records: list[CorpusRecord],
    hymn_html: str,
    error: str = "",
) -> SampleResult:
    missing_verse = sum(1 for record in records if not record.verse_text)
    missing_pozh = sum(1 for record in records if not record.pozhppurai)
    missing_kuri = sum(1 for record in records if not record.kurippurai)
    commentary_count = sum(1 for record in records if record.commentary_url)
    anomalies = detect_record_anomalies(records, hymn_html)
    if missing_verse:
        anomalies.append(f"missing_verse_text:{missing_verse}")
    if missing_pozh:
        anomalies.append(f"missing_pozhppurai:{missing_pozh}")
    if missing_kuri:
        anomalies.append(f"missing_kurippurai:{missing_kuri}")
    if error:
        anomalies.append("extraction_failure")

    return SampleResult(
        hymn_id=hymn.hymn_id,
        hymn_title=records[0].hymn_title if records else hymn.title,
        hymn_url=hymn.url,
        sample_group=group,
        verse_count=len(records),
        commentary_count=commentary_count,
        missing_verse_text=missing_verse,
        missing_pozhppurai=missing_pozh,
        missing_kurippurai=missing_kuri,
        success=not error and missing_verse == 0 and missing_pozh == 0 and missing_kuri == 0,
        anomalies=sorted(set(anomalies)),
        error=error,
    )


def summarize_sample(results: list[SampleResult]) -> SampleSummary:
    sampled = len(results)
    successful = sum(1 for result in results if result.success)
    failed = sampled - successful
    average_verses = sum(result.verse_count for result in results) / sampled if sampled else 0.0
    coverage_values = [
        result.commentary_count / result.verse_count
        for result in results
        if result.verse_count > 0
    ]
    average_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0.0
    return SampleSummary(
        sampled_hymns=sampled,
        successful_hymns=successful,
        failed_hymns=failed,
        average_verses_per_hymn=average_verses,
        average_commentary_coverage=average_coverage,
    )


def render_report(
    hymn_links: list[HymnLink],
    selected: list[tuple[str, HymnLink]],
    results: list[SampleResult],
    summary: SampleSummary,
) -> str:
    lines = [
        "# Corpus Validation Sampling Report",
        "",
        f"- Navigation URL: `{LEFT_FRAME_URL}`",
        f"- Valid hymn links discovered: `{len(hymn_links)}`",
        f"- Sample strategy: first `{DEFAULT_SAMPLE_GROUP_SIZE}`, middle `{DEFAULT_SAMPLE_GROUP_SIZE}`, last `{DEFAULT_SAMPLE_GROUP_SIZE}` hymns",
        f"- Sampled hymns: `{summary.sampled_hymns}`",
        f"- Successful hymns: `{summary.successful_hymns}`",
        f"- Failed hymns: `{summary.failed_hymns}`",
        f"- Average verses per hymn: `{summary.average_verses_per_hymn:.2f}`",
        f"- Average commentary coverage: `{summary.average_commentary_coverage:.2%}`",
        "",
        "## Sampled Hymns",
        "",
        "| Group | Hymn ID | Title | URL |",
        "| --- | --- | --- | --- |",
    ]
    for group, hymn in selected:
        title = hymn.title.replace("|", "\\|")
        lines.append(f"| {group} | `{hymn.hymn_id}` | {title} | `{hymn.url}` |")

    lines.extend(
        [
            "",
            "## Results",
            "",
            "| Group | Hymn ID | Success | Verses | Commentary | Missing Verse | Missing Pozhppurai | Missing Kurippurai | Anomalies |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for result in results:
        anomalies = ", ".join(result.anomalies) if result.anomalies else "none"
        anomalies = anomalies.replace("|", "\\|")
        lines.append(
            "| "
            f"{result.sample_group} | `{result.hymn_id}` | `{result.success}` | "
            f"{result.verse_count} | {result.commentary_count} | "
            f"{result.missing_verse_text} | {result.missing_pozhppurai} | {result.missing_kurippurai} | "
            f"{anomalies} |"
        )

    failures = [result for result in results if result.error]
    if failures:
        lines.extend(["", "## Failures", ""])
        for result in failures:
            lines.append(f"- `{result.hymn_id}`: {result.error}")

    return "\n".join(lines)


def run_validation_sample(
    left_frame_url: str,
    output_dir: Path,
    delay: float,
    timeout: int,
    resume: bool,
    group_size: int,
) -> tuple[list[HymnLink], list[tuple[str, HymnLink]], list[SampleResult], SampleSummary]:
    nav_raw_dir = resolve_output_path(output_dir, DEFAULT_NAV_RAW_RELATIVE)
    hymn_raw_dir = resolve_output_path(output_dir, DEFAULT_HYMN_RAW_RELATIVE)
    commentary_raw_dir = resolve_output_path(output_dir, DEFAULT_COMMENTARY_RAW_RELATIVE)

    left_html = fetch_or_read_snapshot(left_frame_url, nav_raw_dir, timeout=timeout, resume=resume)
    hymn_links = extract_hymn_links(left_frame_url, left_html)
    selected = select_sample_hymns(hymn_links, group_size=group_size)

    results: list[SampleResult] = []
    for index, (group, hymn) in enumerate(selected, start=1):
        if index > 1 and delay > 0:
            time.sleep(delay)
        hymn_html = ""
        records: list[CorpusRecord] = []
        error = ""
        try:
            _title, records = scrape_hymn(
                hymn,
                delay=delay,
                timeout=timeout,
                hymn_raw_dir=hymn_raw_dir,
                commentary_raw_dir=commentary_raw_dir,
                resume=resume,
            )
            hymn_path = snapshot_path_for(hymn.url, hymn_raw_dir)
            hymn_html = hymn_path.read_text(encoding="utf-8") if hymn_path.exists() else ""
        except Exception as exc:
            error = str(exc)
        results.append(summarize_records(hymn, group, records, hymn_html, error=error))

    summary = summarize_sample(results)
    return hymn_links, selected, results, summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a first/middle/last sample of Irandaam Thirumurai hymns")
    parser.add_argument("--left-frame-url", default=LEFT_FRAME_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_RELATIVE)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--group-size", type=int, default=DEFAULT_SAMPLE_GROUP_SIZE)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_path = resolve_output_path(args.output_dir, args.report)
    try:
        hymn_links, selected, results, summary = run_validation_sample(
            left_frame_url=args.left_frame_url,
            output_dir=args.output_dir,
            delay=args.delay,
            timeout=args.timeout,
            resume=not args.no_resume,
            group_size=args.group_size,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(hymn_links, selected, results, summary), encoding="utf-8")

    print(f"Discovered {len(hymn_links)} valid hymn links")
    print(f"Sampled {summary.sampled_hymns} hymns")
    print(f"Successful hymns: {summary.successful_hymns}")
    print(f"Failed hymns: {summary.failed_hymns}")
    print(f"Report written to {report_path}")
    return 0 if summary.failed_hymns == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
